/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { CardLayout } from './CardLayout';
import type { FormFieldGroup } from './FormFieldGroup';

export type RegisterFormTemplate_In = {
    name: string;
    description?: string;
    field_groups?: Array<FormFieldGroup>;
    card_layout?: CardLayout;
    logo?: string;
};
