/* tslint:disable */
/* eslint-disable */
/**
/* This file was automatically generated from pydantic models by running pydantic2ts.
/* Do not modify it by hand - just update the pydantic models and then re-run the script
*/

export interface LoginCredentials {
  username: string;
  password: string;
}
export interface LoginResponseData {
  token: string;
  profile: Profile;
}
export interface Profile {
  /**
   * Appears in model without the underscore, but stored with it.
   */
  _id: number;
  username: string;
  age?: number;
  hobbies: string[];
}
