/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';

export class InternalService {

    /**
     * Drop Database
     * Drop the database
     * @returns void
     * @throws ApiError
     */
    public static dropDatabase(): CancelablePromise<void> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/database',
        });
    }

    /**
     * Read Root
     * @returns string Successful Response
     * @throws ApiError
     */
    public static readRootGet(): CancelablePromise<string> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/',
        });
    }

}