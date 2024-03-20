/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { Guardian } from './Guardian';
import type { PatientRequests } from './PatientRequests';

export type RegisterPatientProfile_In = {
    _id: string;
    name: string;
    primary_cancer_diagnosis: string;
    social_worker_name: string;
    social_worker_organization: string;
    date_of_diagnosis: string;
    age: number;
    guardians: Array<Guardian>;
    household_details: string;
    family_net_monthly_income: number;
    address: string;
    recent_requests: Array<PatientRequests>;
};
