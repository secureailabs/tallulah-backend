/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { UserRole } from './UserRole';

export type UserInfo_Out = {
    name: string;
    organization: string;
    email: string;
    job_title: string;
    roles: Array<UserRole>;
    avatar?: string;
    _id: string;
};
