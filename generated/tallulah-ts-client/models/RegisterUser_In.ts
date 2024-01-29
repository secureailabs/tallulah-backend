/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { UserRole } from './UserRole';

export type RegisterUser_In = {
    name: string;
    organization: string;
    email: string;
    job_title: string;
    roles: Array<UserRole>;
    avatar?: string;
    password: string;
};
