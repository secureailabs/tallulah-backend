/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { EmailState } from './EmailState';

export type GetEmail_Out = {
    subject: string;
    body: any;
    from_address: any;
    received_time: string;
    mailbox_id: string;
    note?: string;
    message_state?: EmailState;
    _id: string;
    creation_time: string;
};
