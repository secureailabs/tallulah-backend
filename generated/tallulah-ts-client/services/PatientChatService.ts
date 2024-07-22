/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { PatientChat_Base } from '../models/PatientChat_Base';
import type { PatientChat_Out } from '../models/PatientChat_Out';

import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';

export class PatientChatService {

    /**
     * Start Patient Chat
     * Start patient chat
     * @param requestBody
     * @returns PatientChat_Out Successful Response
     * @throws ApiError
     */
    public static startPatientChat(
        requestBody: PatientChat_Base,
    ): CancelablePromise<PatientChat_Out> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/patient-chat/',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                404: `Chat not found`,
                422: `Validation Error`,
            },
        });
    }

    /**
     * Patient Chat
     * Ask a query
     * @param chatId Chat Id
     * @param requestBody
     * @returns PatientChat_Out Successful Response
     * @throws ApiError
     */
    public static patientChat(
        chatId: string,
        requestBody: string,
    ): CancelablePromise<PatientChat_Out> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/patient-chat/{chat_id}',
            path: {
                'chat_id': chatId,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                404: `Chat not found`,
                422: `Validation Error`,
            },
        });
    }

    /**
     * Init Data
     * Initialize test data
     * @returns any Successful Response
     * @throws ApiError
     */
    public static initData(): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/patient-chat/test/init',
        });
    }

}