/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { app__models__form_templates__CardLayout } from './app__models__form_templates__CardLayout';
import type { FormFieldGroup } from './FormFieldGroup';
import type { FormTemplateState } from './FormTemplateState';

export type GetFormTemplate_Out = {
    name: string;
    description?: string;
    field_groups?: Array<FormFieldGroup>;
    card_layout?: app__models__form_templates__CardLayout;
    logo?: string;
    _id: string;
    creation_time?: string;
    state: FormTemplateState;
    last_edit_time?: string;
};
