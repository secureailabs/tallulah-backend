/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { EmailBody } from './EmailBody';

export type GetResponseTemplate_Out = {
    name: string;
    subject?: string;
    body?: EmailBody;
    note?: string;
    _id: string;
    creation_time?: string;
    last_edit_time?: string;
};
