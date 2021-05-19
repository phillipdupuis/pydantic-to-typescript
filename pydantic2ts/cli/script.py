import importlib
import inspect
import json
import logging
import os
import shutil
import sys
from importlib.util import spec_from_file_location, module_from_spec
from tempfile import mkdtemp
from types import ModuleType
from typing import Type, Dict, Any, List, Tuple
from uuid import uuid4

import click
from pydantic import BaseModel, Extra, create_model

try:
    from pydantic.generics import GenericModel
except ImportError:
    GenericModel = None

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(message)s")

logger = logging.getLogger("pydantic2ts")


def import_module(path: str) -> ModuleType:
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
            module = module_from_spec(spec)
            sys.modules[name] = module
            spec.loader.exec_module(module)
            return module
        else:
            return importlib.import_module(path)
    except BaseException as e:
        logger.error(
            "The --module argument must be a module path separated by dots or a valid filepath"
        )
        raise e


def is_submodule(obj, module_name: str) -> bool:
    """
    Return true if an object is a submodule
    """
    return inspect.ismodule(obj) and getattr(obj, "__name__", "").startswith(
        f"{module_name}."
    )


def is_concrete_pydantic_model(obj) -> bool:
    """
    Return true if an object is a concrete subclass of pydantic's BaseModel.
    'concrete' meaning that it's not a GenericModel.
    """
    if not inspect.isclass(obj):
        return False
    elif obj is BaseModel:
        return False
    elif GenericModel and issubclass(obj, GenericModel):
        return bool(obj.__concrete__)
    else:
        return issubclass(obj, BaseModel)


def extract_pydantic_models(module: ModuleType) -> List[Type[BaseModel]]:
    """
    Given a module, return a list of the pydantic models contained within it.
    """
    models = []
    module_name = module.__name__

    for _, model in inspect.getmembers(module, is_concrete_pydantic_model):
        models.append(model)

    for _, submodule in inspect.getmembers(
        module, lambda obj: is_submodule(obj, module_name)
    ):
        models.extend(extract_pydantic_models(submodule))

    return models


def remove_master_model_from_output(output: str) -> None:
    """
    A faux 'master model' with references to all the pydantic models is necessary for generating
    clean typescript definitions without any duplicates, but we don't actually want it in the
    output. This function handles removing it from the generated typescript file.
    """
    with open(output, "r") as f:
        lines = f.readlines()

    start, end = None, None
    for i, line in enumerate(lines):
        if line.rstrip("\r\n") == "export interface _Master_ {":
            start = i
        elif (start is not None) and line.rstrip("\r\n") == "}":
            end = i
            break

    new_lines = lines[:start] + lines[(end + 1) :]
    with open(output, "w") as f:
        f.writelines(new_lines)


def clean_schema(schema: Dict[str, Any]) -> None:
    """
    Clean up the resulting JSON schemas by:

    1) Removing titles from JSON schema properties.
       If we don't do this, each property will have its own interface in the
       resulting typescript file (which is a LOT of unnecessary noise).
    2) Getting rid of the useless "An enumeration." description applied to Enums
       which don't have a docstring.
    """
    for prop in schema.get("properties", {}).values():
        prop.pop("title", None)

    if "enum" in schema and schema.get("description") == "An enumeration.":
        del schema["description"]


def generate_json_schema(models: List[Type[BaseModel]]) -> str:
    """
    Create a top-level '_Master_' model with references to each of the actual models.
    Generate the schema for this model, which will include the schemas for all the
    nested models. Then clean up the schema.

    One weird thing we do is we temporarily override the 'extra' setting in models,
    changing it to 'forbid' UNLESS it was explicitly set to 'allow'. This prevents
    '[k: string]: any' from being added to every interface. This change is reverted
    once the schema has been generated.
    """
    model_extras = [getattr(m.Config, "extra", None) for m in models]

    try:
        for m in models:
            if getattr(m.Config, "extra", None) != Extra.allow:
                m.Config.extra = Extra.forbid

        master_model = create_model(
            "_Master_", **{m.__name__: (m, ...) for m in models}
        )
        master_model.Config.extra = Extra.forbid
        master_model.Config.schema_extra = staticmethod(clean_schema)

        schema = json.loads(master_model.schema_json())

        for d in schema.get("definitions", {}).values():
            clean_schema(d)

        return json.dumps(schema, indent=2)

    finally:
        for m, x in zip(models, model_extras):
            if x is not None:
                m.Config.extra = x


def generate_typescript_defs(
    module: str, output: str, exclude: Tuple[str] = (), json2ts_cmd: str = "json2ts"
) -> None:
    """
    Convert the pydantic models in a python module into typescript interfaces.

    :param module: python module containing pydantic model definitions, ex: my_project.api.schemas
    :param output: file that the typescript definitions will be written to
    :param exclude: optional, a tuple of names for pydantic models which should be omitted from the typescript output.
    :param json2ts_cmd: optional, the command that will execute json2ts. Use this if it's installed in a strange spot.
    """
    if not shutil.which(json2ts_cmd):
        raise Exception(
            "json2ts must be installed. Instructions can be found here: "
            "https://www.npmjs.com/package/json-schema-to-typescript"
        )

    logger.info("Finding pydantic models...")

    models = extract_pydantic_models(import_module(module))

    if exclude:
        models = [m for m in models if m.__name__ not in exclude]

    logger.info("Generating JSON schema from pydantic models...")

    schema = generate_json_schema(models)
    schema_dir = mkdtemp()
    schema_file_path = os.path.join(schema_dir, "schema.json")

    with open(schema_file_path, "w") as f:
        f.write(schema)

    logger.info("Converting JSON schema to typescript definitions...")

    banner_comment = "\n".join(
        [
            "/* tslint:disable */",
            "/* eslint-disable */",
            "/**",
            "/* This file was automatically generated from pydantic models by running pydantic2ts.",
            "/* Do not modify it by hand - just update the pydantic models and then re-run the script",
            "*/",
        ]
    )
    os.system(
        f'{json2ts_cmd} -i {schema_file_path} -o {output} --bannerComment "{banner_comment}"'
    )
    shutil.rmtree(schema_dir)
    remove_master_model_from_output(output)

    logger.info(f"Saved typescript definitions to {output}.")


@click.command()
@click.option(
    "--module",
    help="name or filepath of the python module. Discoverable submodules will also be checked",
)
@click.option(
    "--output", help="name of the file the typescript definitions should be written to"
)
@click.option(
    "--exclude",
    multiple=True,
    help="name of a pydantic model which should be omitted from the results. This option can be defined multiple times",
)
@click.option("--json2ts-cmd", default="json2ts")
def main(
    module: str, output: str, exclude: Tuple[str], json2ts_cmd: str = "json2ts"
) -> None:
    """
    CLI entrypoint to run :func:`generate_typescript_defs`
    """
    return generate_typescript_defs(module, output, exclude, json2ts_cmd)


if __name__ == "__main__":
    main()
