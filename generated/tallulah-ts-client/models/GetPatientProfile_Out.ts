/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { Guardian } from './Guardian';
import type { PatientProfileState } from './PatientProfileState';
import type { PatientRequests } from './PatientRequests';

export type GetPatientProfile_Out = {
    patient_id: string;
    repository_id: string;
    name: string;
    race?: string;
    ethnicity?: string;
    gender?: string;
    primary_cancer_diagnosis?: string;
    social_worker_name?: string;
    social_worker_organization?: string;
    date_of_diagnosis?: string;
    age?: number;
    guardians?: Array<Guardian>;
    household_details?: string;
    family_net_monthly_income?: number;
    address?: string;
    recent_requests?: Array<PatientRequests>;
    photos?: Array<string>;
    videos?: Array<string>;
    notes?: string;
    tags?: Array<string>;
    id: string;
    creation_time?: string;
    state?: PatientProfileState;
    organization_id: string;
    owner_id: string;
};
