/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { GetMultiplePatientProfiles_Out } from '../models/GetMultiplePatientProfiles_Out';
import type { GetPatientProfile_Out } from '../models/GetPatientProfile_Out';
import type { RegisterPatientProfile_In } from '../models/RegisterPatientProfile_In';
import type { RegisterPatientProfile_Out } from '../models/RegisterPatientProfile_Out';
import type { UpdatePatientProfile_In } from '../models/UpdatePatientProfile_In';

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

    /**
     * Search Patient Profiles
     * Search the text from patient profiles for the current user for the template
     * @param searchQuery Search query
     * @returns any Successful Response
     * @throws ApiError
     */
    public static searchPatientProfiles(
        searchQuery: string,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/patient-profiles/search',
            query: {
                'search_query': searchQuery,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }

    /**
     * Get Patient Profile
     * Get a patient profile by id
     * @param patientProfileId Patient profile id
     * @returns GetPatientProfile_Out Successful Response
     * @throws ApiError
     */
    public static getPatientProfile(
        patientProfileId: string,
    ): CancelablePromise<GetPatientProfile_Out> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/patient-profiles/{patient_profile_id}',
            path: {
                'patient_profile_id': patientProfileId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }

    /**
     * Update Patient Profile
     * Update a patient profile by id
     * @param patientProfileId Patient profile id
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static updatePatientProfile(
        patientProfileId: string,
        requestBody: UpdatePatientProfile_In,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'PUT',
            url: '/api/patient-profiles/{patient_profile_id}',
            path: {
                'patient_profile_id': patientProfileId,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }

    /**
     * Delete Patient Profile
     * Delete a patient profile by id
     * @param patientProfileId Patient profile id
     * @returns any Successful Response
     * @throws ApiError
     */
    public static deletePatientProfile(
        patientProfileId: string,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/api/patient-profiles/{patient_profile_id}',
            path: {
                'patient_profile_id': patientProfileId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }

}