# pydantic-to-typescript

A simple CLI tool for converting pydantic models into typescript interfaces. Useful for any scenario in which python and javascript applications are interacting, since it allows you to have a single source of truth for type definitions.

This tool requires that you have the lovely json2ts CLI utility installed. Instructions can be found here: https://www.npmjs.com/package/json-schema-to-typescript

### Installation
```bash
$ pip install pydantic-to-typescript
```
---
### CLI

|Prop|Description|
|:----------|:-----------|
|`--module`|name of the python module you would like to convert. All the pydantic models within it will be converted to typescript interfaces. Discoverable submodules will also be checked. Ex: 'pydantic2ts.examples.pydantic_models'|
|`--output`|name of the file the typescript definitions should be written to. Ex: './frontend/apiTypes.ts'|
|<nobr>`--json2ts-cmd`</nobr>|optional, the command used to invoke json2ts. The default is 'json2ts'. Specify this if you have it installed in a strange location and need to provide the exact path (ex: /myproject/node_modules/bin/json2ts)|
---
### Usage
pydantic2ts/examples/pydantic_models.py:
```python
from pydantic import BaseModel, Extra
from enum import Enum
from typing import List, Dict


class NoExtraProps:
    extra = Extra.forbid


class Sport(str, Enum):
    football = 'football'
    basketball = 'basketball'


class Athlete(BaseModel):
    name: str
    age: int
    sports: List[Sport]
    Config = NoExtraProps


class Team(BaseModel):
    name: str
    sport: Sport
    athletes: List[Athlete]
    Config = NoExtraProps


class League(BaseModel):
    cities: Dict[str, Team]
    Config = NoExtraProps
```
Command-line:
```bash
$ pydantic2ts --module pydantic2ts.examples.pydantic_models --output output.ts
```
output.ts:
```
/* tslint:disable */
/**
/* This file was automatically generated from pydantic models by running pydantic2ts.
/* Do not modify it by hand - just update the pydantic models and then re-run the script
*/

export interface Athlete {
  name: string;
  age: number;
  sports: ("football" | "basketball")[];
}
export interface League {
  cities: {
    [k: string]: Team;
  };
}
export interface Team {
  name: string;
  sport: "football" | "basketball";
  athletes: Athlete[];
}
```