/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { Annotation } from './Annotation';
import type { EmailState } from './EmailState';

export type GetEmail_Out = {
    subject?: string;
    body?: any;
    from_address: any;
    received_time: string;
    mailbox_id: string;
    user_id: string;
    label?: string;
    annotations?: Array<Annotation>;
    note?: string;
    message_state?: EmailState;
    outlook_id: string;
    id: string;
    creation_time: string;
};
