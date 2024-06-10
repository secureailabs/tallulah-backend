/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ETapestryDataState } from './ETapestryDataState';

export type UpdateETapestryData_In = {
    state?: ETapestryDataState;
    notes?: string;
    tags?: Array<string>;
    photos?: Array<string>;
    videos?: Array<string>;
};
