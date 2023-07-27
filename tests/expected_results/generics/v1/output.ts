/* tslint:disable */
/* eslint-disable */
/**
/* This file was automatically generated from pydantic models by running pydantic2ts.
/* Do not modify it by hand - just update the pydantic models and then re-run the script
*/

export interface Article {
  author: User;
  content: string;
  published: string;
}
export interface User {
  name: string;
  email: string;
}
export interface Error {
  code: number;
  message: string;
}
export interface ListArticlesResponse {
  data?: Article[];
  error?: Error;
}
export interface ListUsersResponse {
  data?: User[];
  error?: Error;
}
export interface UserProfile {
  name: string;
  email: string;
  joined: string;
  last_active: string;
  age: number;
}
export interface UserProfileResponse {
  data?: UserProfile;
  error?: Error;
}
