/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { CardLayout } from './CardLayout';
import type { FormFieldGroup } from './FormFieldGroup';
import type { FormTemplateState } from './FormTemplateState';

export type GetFormTemplate_Out = {
    name: string;
    description?: string;
    field_groups?: Array<FormFieldGroup>;
    card_layout?: CardLayout;
    logo?: string;
    _id: string;
    creation_time?: string;
    state: FormTemplateState;
    last_edit_time?: string;
};
