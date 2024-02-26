/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ParametersType } from './ParametersType';

export type ParameterField = {
    name: string;
    label: string;
    description?: string;
    place_holder?: string;
    type?: ParametersType;
    required?: boolean;
    options?: Array<string>;
};
