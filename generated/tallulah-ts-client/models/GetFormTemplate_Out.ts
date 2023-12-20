/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { FormField } from './FormField';
import type { FormTemplateState } from './FormTemplateState';

export type GetFormTemplate_Out = {
    name: string;
    description?: string;
    fields?: Array<FormField>;
    _id: string;
    creation_time?: string;
    state: FormTemplateState;
    last_edit_time?: string;
};
