/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { GetEmail_Out } from './GetEmail_Out';

export type GetMultipleEmail_Out = {
    messages: Array<GetEmail_Out>;
    next: number;
    limit: number;
};
