/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { Context } from './Context';
import type { ParameterField } from './ParameterField';

export type UpdateContentGenerationTemplate_In = {
    name?: string;
    description?: string;
    parameters?: Array<ParameterField>;
    context?: Array<Context>;
    prompt?: string;
};
