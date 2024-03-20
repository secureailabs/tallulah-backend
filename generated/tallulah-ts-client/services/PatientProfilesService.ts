/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { GetMultiplePatientProfiles_Out } from '../models/GetMultiplePatientProfiles_Out';
import type { RegisterPatientProfile_In } from '../models/RegisterPatientProfile_In';
import type { RegisterPatientProfile_Out } from '../models/RegisterPatientProfile_Out';

import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';

export class PatientProfilesService {

    /**
     * Get All Patient Profiles
     * Get all the patient profiles owned by the current user with pagination
     * @param skip Number of patient profiles to skip
     * @param limit Number of patient profiles to return
     * @param sortKey Sort key
     * @param sortDirection Sort direction
     * @returns GetMultiplePatientProfiles_Out Successful Response
     * @throws ApiError
     */
    public static getAllPatientProfiles(
        skip?: number,
        limit: number = 20,
        sortKey: string = 'creation_time',
        sortDirection: number = -1,
    ): CancelablePromise<GetMultiplePatientProfiles_Out> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/patient-profiles/',
            query: {
                'skip': skip,
                'limit': limit,
                'sort_key': sortKey,
                'sort_direction': sortDirection,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }

    /**
     * Add New Patient Profile
     * Add a new patient profile
     * @param requestBody
     * @returns RegisterPatientProfile_Out Successful Response
     * @throws ApiError
     */
    public static addPatientProfile(
        requestBody: RegisterPatientProfile_In,
    ): CancelablePromise<RegisterPatientProfile_Out> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/patient-profiles/',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }

}