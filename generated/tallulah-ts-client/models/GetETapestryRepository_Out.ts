/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { app__models__etapestry_repositories__CardLayout } from './app__models__etapestry_repositories__CardLayout';
import type { ETapestryRepositoryState } from './ETapestryRepositoryState';

export type GetETapestryRepository_Out = {
    name: string;
    description: string;
    card_layout?: app__models__etapestry_repositories__CardLayout;
    _id: string;
    user_id: string;
    organization: string;
    last_refresh_time: string;
    state: ETapestryRepositoryState;
    creation_time?: string;
};
