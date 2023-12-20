/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { FormFieldTypes } from './FormFieldTypes';

export type FormField = {
    name: string;
    description?: string;
    place_holder?: string;
    type?: FormFieldTypes;
    required?: boolean;
    options?: Array<string>;
};
