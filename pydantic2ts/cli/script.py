import argparse
import importlib
import inspect
import json
import logging
import os
import shutil
import sys
from contextlib import ExitStack, contextmanager
from importlib.util import module_from_spec, spec_from_file_location
from tempfile import mkdtemp
from types import ModuleType
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    Generator,
    List,
    Optional,
    Tuple,
    Type,
    Union,
)
from uuid import uuid4

import pydantic2ts.pydantic_v1 as v1
import pydantic2ts.pydantic_v2 as v2

if TYPE_CHECKING:  # pragma: no cover
    from pydantic.config import ConfigDict
    from pydantic.v1.config import BaseConfig
    from pydantic.v1.fields import ModelField


LOG = logging.getLogger("pydantic2ts")

_USELESS_ENUM_DESCRIPTION = "An enumeration."
_USELESS_STR_DESCRIPTION = inspect.getdoc(str)


def _import_module(path: str) -> ModuleType:
    """
    Helper which allows modules to be specified by either dotted path notation or by filepath.

    If we import by filepath, we must also assign a name to it and add it to sys.modules BEFORE
    calling 'spec.loader.exec_module' because there is code in pydantic which requires that the
    definition exist in sys.modules under that name.
    """
    try:
        if os.path.exists(path):
            name = uuid4().hex
            spec = spec_from_file_location(name, path, submodule_search_locations=[])
            assert spec is not None, f"spec_from_file_location failed for {path}"
            module = module_from_spec(spec)
            sys.modules[name] = module
            assert spec.loader is not None, f"loader is None for {path}"
            spec.loader.exec_module(module)
            return module
        else:
            return importlib.import_module(path)
    except Exception as e:
        LOG.error(
            "The --module argument must be a module path separated by dots or a valid filepath"
        )
        raise e


def _is_submodule(obj: Any, module_name: str) -> bool:
    """
    Return true if an object is a submodule
    """
    return inspect.ismodule(obj) and getattr(obj, "__name__", "").startswith(f"{module_name}.")


def _is_v1_model(obj: Any) -> bool:
    """
    Return true if an object is a 'concrete' pydantic V1 model.
    """
    if not inspect.isclass(obj):
        return False
    elif obj is v1.BaseModel:
        return False
    elif v1.GenericModel and issubclass(obj, v1.GenericModel):
        return bool(obj.__concrete__)
    else:
        return issubclass(obj, v1.BaseModel)


def _is_v2_model(obj: Any) -> bool:
    """
    Return true if an object is a 'concrete' pydantic V2 model.
    """
    if not v2.enabled:
        return False
    elif not inspect.isclass(obj):
        return False
    elif obj is v2.BaseModel:
        return False
    elif not issubclass(obj, v2.BaseModel):
        return False
    generic_metadata = getattr(obj, "__pydantic_generic_metadata__", {})
    generic_parameters = generic_metadata.get("parameters")
    return not generic_parameters


def _is_pydantic_model(obj: Any) -> bool:
    """
    Return true if an object is a concrete model for either V1 or V2 of pydantic.
    """
    return _is_v1_model(obj) or _is_v2_model(obj)


def _is_nullable(schema: Dict[str, Any]) -> bool:
    """
    Return true if a JSON schema has 'null' as one of its types.
    """
    if schema.get("type") == "null":
        return True
    if isinstance(schema.get("type"), list) and "null" in schema["type"]:
        return True
    if isinstance(schema.get("anyOf"), list):
        return any(_is_nullable(s) for s in schema["anyOf"])
    return False


def _get_model_config(model: Type[Any]) -> "Union[ConfigDict, Type[BaseConfig]]":
    """
    Return the 'config' for a pydantic model.
    In version 1 of pydantic, this is a class. In version 2, it's a dictionary.
    """
    if hasattr(model, "Config") and inspect.isclass(model.Config):
        return model.Config
    return model.model_config


def _get_model_json_schema(model: Type[Any]) -> Dict[str, Any]:
    """
    Generate the JSON schema for a pydantic model.
    """
    if _is_v1_model(model):
        return json.loads(model.schema_json())
    return model.model_json_schema(mode="serialization")


def _extract_pydantic_models(module: ModuleType) -> List[type]:
    """
    Given a module, return a list of the pydantic models contained within it.
    """
    models: List[type] = []
    module_name = module.__name__

    for _, model in inspect.getmembers(module, _is_pydantic_model):
        models.append(model)

    for _, submodule in inspect.getmembers(module, lambda obj: _is_submodule(obj, module_name)):
        models.extend(_extract_pydantic_models(submodule))

    return models


def _clean_json_schema(schema: Dict[str, Any], model: Any = None) -> None:
    """
    Clean up the resulting JSON schemas via the following steps:

    1) Get rid of descriptions that are auto-generated and just add noise:
        - "An enumeration." for Enums
        - `inspect.getdoc(str)` for Literal types
    2) Remove titles from JSON schema properties.
       If we don't do this, each property will have its own interface in the
       resulting typescript file (which is a LOT of unnecessary noise).
    3) If it's a V1 model, ensure that nullability is properly represented.
       https://github.com/pydantic/pydantic/issues/1270
    """
    description = schema.get("description")

    if "enum" in schema and description == _USELESS_ENUM_DESCRIPTION:
        del schema["description"]
    elif description == _USELESS_STR_DESCRIPTION:
        del schema["description"]

    properties: Dict[str, Dict[str, Any]] = schema.get("properties", {})

    for prop in properties.values():
        prop.pop("title", None)

    if _is_v1_model(model):
        fields: List["ModelField"] = list(model.__fields__.values())
        fields_that_should_be_nullable = [f for f in fields if f.allow_none]
        for field in fields_that_should_be_nullable:
            try:
                name = field.alias
                prop = properties.get(field.alias)
                if prop and not _is_nullable(prop):
                    properties[name] = {"anyOf": [prop, {"type": "null"}]}
            except Exception:
                LOG.error(
                    f"Failed to ensure nullability for field {field.alias}.",
                    exc_info=True,
                )


def _clean_output_file(output_filename: str) -> None:
    """
    Clean up the resulting typescript definitions via the following steps:

    1. Remove the "_Master_" model.
       It exists solely to serve as a namespace for the target models.
       By rolling them all up into a single model, we can generate a single output file.
    2. Add a banner comment with clear instructions for regenerating the typescript definitions.
    """
    with open(output_filename, "r") as f:
        lines = f.readlines()

    start, end = None, None
    for i, line in enumerate(lines):
        if line.rstrip("\r\n") == "export interface _Master_ {":
            start = i
        elif (start is not None) and line.rstrip("\r\n") == "}":
            end = i
            break

    assert start is not None, "Could not find the start of the _Master_ interface."
    assert end is not None, "Could not find the end of the _Master_ interface."

    banner_comment_lines = [
        "/* tslint:disable */\n",
        "/* eslint-disable */\n",
        "/**\n",
        "/* This file was automatically generated from pydantic models by running pydantic2ts.\n",
        "/* Do not modify it by hand - just update the pydantic models and then re-run the script\n",
        "*/\n\n",
    ]

    new_lines = banner_comment_lines + lines[:start] + lines[(end + 1) :]

    with open(output_filename, "w") as f:
        f.writelines(new_lines)


@contextmanager
def _schema_generation_overrides(
    model: Type[Any],
) -> Generator[None, None, None]:
    """
    Temporarily override the 'extra' setting for a model,
    changing it to 'forbid' unless it was EXPLICITLY set to 'allow'.
    This prevents '[k: string]: any' from automatically being added to every interface.
    """
    revert: Dict[str, Any] = {}
    config = _get_model_config(model)
    try:
        if isinstance(config, dict):
            if config.get("extra") != "allow":
                revert["extra"] = config.get("extra")
                config["extra"] = "forbid"
        else:
            if config.extra != "allow":
                revert["extra"] = config.extra
                config.extra = "forbid"  # type: ignore
        yield
    finally:
        for key, value in revert.items():
            if isinstance(config, dict):
                config[key] = value
            else:
                setattr(config, key, value)


def _generate_json_schema(models: List[type]) -> str:
    """
    Create a top-level '_Master_' model with references to each of the actual models.
    Generate the schema for this model, which will include the schemas for all the
    nested models. Then clean up the schema.
    """
    with ExitStack() as stack:
        models_by_name: Dict[str, type] = {}
        models_as_fields: Dict[str, Tuple[type, Any]] = {}

        for model in models:
            stack.enter_context(_schema_generation_overrides(model))
            name = model.__name__
            models_by_name[name] = model
            models_as_fields[name] = (model, ...)

        use_v1_tools = any(issubclass(m, v1.BaseModel) for m in models)
        create_model = v1.create_model if use_v1_tools else v2.create_model  # type: ignore
        master_model = create_model("_Master_", **models_as_fields)  # type: ignore
        master_schema = _get_model_json_schema(master_model)  # type: ignore

        defs_key = "$defs" if "$defs" in master_schema else "definitions"
        defs: Dict[str, Any] = master_schema.get(defs_key, {})

        for name, schema in defs.items():
            _clean_json_schema(schema, models_by_name.get(name))

        return json.dumps(master_schema, indent=2)


def generate_typescript_defs(
    module: str,
    output: str,
    exclude: Tuple[str, ...] = (),
    json2ts_cmd: str = "json2ts",
) -> None:
    """
    Convert the pydantic models in a python module into typescript interfaces.

    :param module: python module containing pydantic model definitions.
                   example: my_project.api.schemas
    :param output: file that the typescript definitions will be written to
    :param exclude: optional, a tuple of names for pydantic models which
                    should be omitted from the typescript output.
    :param json2ts_cmd: optional, the command that will execute json2ts.
                        Provide this if the executable is not discoverable
                        or if it's locally installed (ex: 'yarn json2ts').
    """
    if " " not in json2ts_cmd and not shutil.which(json2ts_cmd):
        raise Exception(
            "json2ts must be installed. Instructions can be found here: "
            "https://www.npmjs.com/package/json-schema-to-typescript"
        )

    LOG.info("Finding pydantic models...")

    models = _extract_pydantic_models(_import_module(module))

    if exclude:
        models = [
            m for m in models if (m.__name__ not in exclude and m.__qualname__ not in exclude)
        ]

    if not models:
        LOG.info("No pydantic models found, exiting.")
        return

    LOG.info("Generating JSON schema from pydantic models...")

    schema = _generate_json_schema(models)
    schema_dir = mkdtemp()
    schema_file_path = os.path.join(schema_dir, "schema.json")

    with open(schema_file_path, "w") as f:
        f.write(schema)

    LOG.info("Converting JSON schema to typescript definitions...")

    json2ts_exit_code = os.system(
        f'{json2ts_cmd} -i {schema_file_path} -o {output} --bannerComment ""'
    )

    shutil.rmtree(schema_dir)

    if json2ts_exit_code == 0:
        _clean_output_file(output)
        LOG.info(f"Saved typescript definitions to {output}.")
    else:
        raise RuntimeError(f'"{json2ts_cmd}" failed with exit code {json2ts_exit_code}.')


def parse_cli_args(args: Optional[List[str]] = None) -> argparse.Namespace:
    """
    Parses the command-line arguments passed to pydantic2ts.
    """
    parser = argparse.ArgumentParser(
        prog="pydantic2ts",
        description=main.__doc__,
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "--module",
        help="name or filepath of the python module.\n"
        "Discoverable submodules will also be checked.",
        required=True,
    )
    parser.add_argument(
        "--output",
        help="name of the file the typescript definitions should be written to.",
        required=True,
    )
    parser.add_argument(
        "--exclude",
        action="append",
        default=[],
        help="name of a pydantic model which should be omitted from the results.\n"
        "This option can be defined multiple times.",
    )
    parser.add_argument(
        "--json2ts-cmd",
        dest="json2ts_cmd",
        default="json2ts",
        help="path to the json-schema-to-typescript executable.\n"
        "Provide this if it's not discoverable or if it's only installed locally (example: 'yarn json2ts').\n"
        "(default: json2ts)",
    )
    return parser.parse_args(args)


def main() -> None:
    """
    CLI entrypoint to run :func:`generate_typescript_defs`
    """
    logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(message)s")
    args = parse_cli_args()
    return generate_typescript_defs(
        args.module,
        args.output,
        tuple(args.exclude),
        args.json2ts_cmd,
    )


if __name__ == "__main__":
    main()
