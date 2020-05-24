# pydantic-to-typescript

A simple CLI tool for converting pydantic models into typescript interfaces. Useful for any scenario in which python and javascript applications are interacting, since it allows you to have a single source of truth for type definitions.

This tool requires that you have the lovely json2ts CLI utility installed. Instructions can be found here: https://www.npmjs.com/package/json-schema-to-typescript

### Installation
```bash
$ pip install pydantic-to-typescript
```

### Command-line usage

|Prop     |Description|
|:--------|:-----------|
|`--module` |name of the python module you would like to convert. All the pydantic models within it will be converted to typescript interfaces. Discoverable submodules will also be checked. Ex: 'pydantic2ts.examples.pydantic_models'|
|`--output` |name of the file the typescript definitions should be written to. Ex: '/frontend/api-types.ts'|
|`--json2ts-cmd` |optional, the command used to invoke json2ts. The default is 'json2ts'. Specify this if you have it installed in a strange location and need to provide the exact path (ex: /myproject/node_modules/bin/json2ts)|

Example:
```bash
$ pydantic2ts --module pydantic2ts.examples.pydantic_models --output output.ts
```
