/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Body_reply_to_emails } from '../models/Body_reply_to_emails';
import type { GetMultipleEmail_Out } from '../models/GetMultipleEmail_Out';

import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';

export class EmailsService {

    /**
     * Get All Emails
     * Get all the emails from the mailbox
     * @param mailboxId Mailbox id
     * @param skip Number of emails to skip
     * @param limit Number of emails to return
     * @param sortKey Sort key
     * @param sortDirection Sort direction
     * @param filterTags Filter tags
     * @returns GetMultipleEmail_Out Successful Response
     * @throws ApiError
     */
    public static getAllEmails(
        mailboxId: string,
        skip?: number,
        limit: number = 20,
        sortKey: string = 'received_time',
        sortDirection: number = -1,
        filterTags?: Array<string>,
    ): CancelablePromise<GetMultipleEmail_Out> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/emails/',
            query: {
                'mailbox_id': mailboxId,
                'skip': skip,
                'limit': limit,
                'sort_key': sortKey,
                'sort_direction': sortDirection,
                'filter_tags': filterTags,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }

    /**
     * Reply To Emails
     * Reply to one email or a tag, or a list of emails or tags
     * @param mailboxId Mailbox id
     * @param emailIds List of email ids
     * @param tags List of tag ids
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static replyToEmails(
        mailboxId: string,
        emailIds?: Array<string>,
        tags?: Array<string>,
        requestBody?: Body_reply_to_emails,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/emails/replies',
            query: {
                'mailbox_id': mailboxId,
                'email_ids': emailIds,
                'tags': tags,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                400: `No emails or tags provided`,
                422: `Validation Error`,
            },
        });
    }

}