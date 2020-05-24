import click
import inspect
import importlib
import os
import shutil
from pydantic import BaseModel, create_model
from typing import Type, Dict, Any
from types import ModuleType


def remove_property_titles(schema: Dict[str, Any], model: Type[BaseModel]) -> None:
    """
    Monkey-patched method for removing titles from JSON schema properties.
    If we don't do this, each property will have its own interface in the
    resulting typescript file (which is a LOT of unnecessary noise).
    """
    for prop in schema.get('properties', {}).values():
        prop.pop('title', None)


def extract_pydantic_models(module: ModuleType):
    """
    Given a module, return a list of the pydantic models contained within it.
    """
    models = []
    for name in dir(module):
        obj = getattr(module, name)
        if (not name.startswith('_'))\
                and inspect.isclass(obj)\
                and issubclass(obj, BaseModel)\
                and obj != BaseModel:
            models.append(obj)
    return models


def remove_master_model_from_output(output: str) -> None:
    """
    A faux 'master model' with references to all the pydantic models is necessary for generating
    clean typescript definitions without any duplicates, but we don't actually want it in the
    output. This function handles removing it from the generated typescript file.
    """
    with open(output, 'r') as f:
        lines = f.readlines()

    start, end = None, None
    for i, line in enumerate(lines):
        if line.rstrip('\r\n') == 'export interface _Master_ {':
            start = i
        elif (start is not None) and line.rstrip('\r\n') == '}':
            end = i
            break

    new_lines = lines[:start] + lines[(end + 1):]
    with open(output, 'w') as f:
        f.writelines(new_lines)


@click.command()
@click.option('--module')
@click.option('--output')
@click.option('--json2ts-cmd', default='json2ts')
def main(
    module: str,
    output: str,
    json2ts_cmd: str = 'json2ts',
) -> None:
    """
    Convert the pydantic models in a python module into typescript interfaces.

    :param module: python module containing pydantic model definitions, ex: my_project.api.schemas
    :param output: file that the typescript definitions will be written to
    :param json2ts_cmd: optional, the command that will execute json2ts. Use this if it's installed in a strange spot.
    """
    if not shutil.which(json2ts_cmd):
        raise Exception('json2ts must be installed. Instructions can be found here: '
                        'https://www.npmjs.com/package/json-schema-to-typescript')

    models = extract_pydantic_models(importlib.import_module(module))

    for m in models:
        m.Config.schema_extra = staticmethod(remove_property_titles)

    master_model = create_model('_Master_', **{m.__name__: (m, ...) for m in models})
    master_model.Config.schema_extra = staticmethod(remove_property_titles)

    with open('schema.json', 'w') as f:
        f.write(master_model.schema_json(indent=2))

    banner_comment = '\n'.join([
        '/* tslint:disable */',
        '/**',
        '/* This file was automatically generated from pydantic models by running pydantic2ts.',
        '/* Do not modify it by hand - just update the pydantic models and then re-run the script',
        '*/',
    ])

    os.system(f'{json2ts_cmd} -i schema.json -o {output} --bannerComment "{banner_comment}"')
    os.remove('schema.json')
    remove_master_model_from_output(output)


if __name__ == '__main__':
    main()
