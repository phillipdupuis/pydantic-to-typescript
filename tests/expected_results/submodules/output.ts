/* tslint:disable */
/* eslint-disable */
/**
/* This file was automatically generated from pydantic models by running pydantic2ts.
/* Do not modify it by hand - just update the pydantic models and then re-run the script
*/

export type CatBreed = "domestic shorthair" | "bengal" | "persian" | "siamese";
export type DogBreed = "mutt" | "labrador" | "golden retriever";

export interface AnimalShelter {
  address: string;
  cats: Cat[];
  dogs: Dog[];
}
export interface Cat {
  name: string;
  age: number;
  declawed: boolean;
  breed: CatBreed;
}
export interface Dog {
  name: string;
  age: number;
  breed: DogBreed;
}
