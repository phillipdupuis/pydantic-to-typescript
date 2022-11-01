/* tslint:disable */
/* eslint-disable */
/**
/* This file was automatically generated from pydantic models by running pydantic2ts.
/* Do not modify it by hand - just update the pydantic models and then re-run the script
*/

export type SomeEnum = "a" | "b";

export interface Foo {
  required: string;
  default: string;
  default_factory: string;
  default_alias_renamed: string;
  optional: string | null;
  optional_nullable: string | null;
  optional_nullable_default: string | null;
  optional_nullable_default_none: string | null;
  optional_default: string | null;
  optional_default_none: string | null;
  union: string | null;
  union_default: string | null;
  union_default_none: string | null;
  optional_union: number | string | null;
  optional_union_default: number | string | null;
  optional_union_default_none: number | string | null;
  some_enum: SomeEnum;
  some_optional_non_primitive?: SomeModel;
}
export interface SomeModel {
  some_optional?: string;
}
