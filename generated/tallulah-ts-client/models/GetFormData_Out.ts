/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { FormDataState } from './FormDataState';

export type GetFormData_Out = {
    form_template_id: string;
    values?: any;
    state?: FormDataState;
    themes?: (Array<string> | null);
    id: string;
    creation_time?: string;
};
