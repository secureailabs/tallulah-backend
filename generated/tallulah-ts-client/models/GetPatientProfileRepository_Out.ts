/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { PatientProfileRepositoryState } from './PatientProfileRepositoryState';

export type GetPatientProfileRepository_Out = {
    name: string;
    description?: string;
    id: string;
    user_id: string;
    organization: string;
    creation_time: string;
    state: PatientProfileRepositoryState;
};
