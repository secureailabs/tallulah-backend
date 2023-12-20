/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { GetFormData_Out } from '../models/GetFormData_Out';
import type { GetMultipleFormData_Out } from '../models/GetMultipleFormData_Out';
import type { RegisterFormData_In } from '../models/RegisterFormData_In';
import type { RegisterFormData_Out } from '../models/RegisterFormData_Out';

import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';

export class FormDataService {

    /**
     * Get All Form Data
     * Get all the form data for the current user for the template
     * @param formTemplateId Form template id
     * @returns GetMultipleFormData_Out Successful Response
     * @throws ApiError
     */
    public static getAllFormData(
        formTemplateId: string,
    ): CancelablePromise<GetMultipleFormData_Out> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/form-data/',
            query: {
                'form_template_id': formTemplateId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }

    /**
     * Add Form Data
     * Add a new form data
     * @param requestBody
     * @returns RegisterFormData_Out Successful Response
     * @throws ApiError
     */
    public static addFormData(
        requestBody: RegisterFormData_In,
    ): CancelablePromise<RegisterFormData_Out> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/form-data/',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }

    /**
     * Get Form Data
     * Get the response data for the form
     * @param formDataId Form data id
     * @returns GetFormData_Out Successful Response
     * @throws ApiError
     */
    public static getFormData(
        formDataId: string,
    ): CancelablePromise<GetFormData_Out> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/form-data/{form_data_id}',
            path: {
                'form_data_id': formDataId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }

    /**
     * Delete Form Data
     * Delete the response template for the current user
     * @param formDataId Form data id
     * @returns void
     * @throws ApiError
     */
    public static deleteFormData(
        formDataId: string,
    ): CancelablePromise<void> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/api/form-data/{form_data_id}',
            path: {
                'form_data_id': formDataId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }

}