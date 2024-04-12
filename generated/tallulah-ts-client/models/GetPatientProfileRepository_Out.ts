/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { app__models__patient_profile_repositories__CardLayout } from './app__models__patient_profile_repositories__CardLayout';
import type { PatientProfileRepositoryState } from './PatientProfileRepositoryState';

export type GetPatientProfileRepository_Out = {
    name: string;
    description?: string;
    card_layout?: app__models__patient_profile_repositories__CardLayout;
    id: string;
    user_id: string;
    organization_id: string;
    creation_time: string;
    state: PatientProfileRepositoryState;
};
