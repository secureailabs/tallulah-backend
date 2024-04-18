/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { DashboardLayout } from './DashboardLayout';
import type { DashboardTemplateState } from './DashboardTemplateState';

export type GetDashboardTemplate_Out = {
    name: string;
    description?: string;
    repository_id: string;
    layout?: DashboardLayout;
    id: string;
    creation_time?: string;
    state: DashboardTemplateState;
    last_edit_time?: string;
};
