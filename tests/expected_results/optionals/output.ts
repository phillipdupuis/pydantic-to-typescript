/* tslint:disable */
/* eslint-disable */
/**
/* This file was automatically generated from pydantic models by running pydantic2ts.
/* Do not modify it by hand - just update the pydantic models and then re-run the script
*/

export type SomeEnum = "a" | "b";

export interface Foo {
  required: string;
  default?: string;
  default_factory?: string;
  default_alias_renamed?: string;
  optional?: string;
  optional_nullable: string;
  optional_nullable_default?: string;
  optional_nullable_default_none?: string;
  optional_default?: string;
  optional_default_none?: string;
  union?: string;
  union_default?: string;
  union_default_none?: string;
  optional_union?: number | string;
  optional_union_default?: number | string;
  optional_union_default_none?: number | string;
  some_enum: SomeEnum;
  some_optional_non_primitive?: SomeModel;
}
export interface SomeModel {
  some_optional?: string;
}
