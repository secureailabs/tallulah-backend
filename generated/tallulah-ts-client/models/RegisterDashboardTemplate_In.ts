/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { DashboardLayout } from './DashboardLayout';

export type RegisterDashboardTemplate_In = {
    name: string;
    description?: string;
    repository_id: string;
    layout?: DashboardLayout;
};
