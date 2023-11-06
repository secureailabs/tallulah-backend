/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
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
            url: '/emails/',
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

}