/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { FormField } from './FormField';

export type FormFieldGroup = {
    name: string;
    description?: string;
    fields?: Array<FormField>;
};
