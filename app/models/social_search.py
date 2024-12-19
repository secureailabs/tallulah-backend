# -------------------------------------------------------------------------------
# Engineering
# social_search.py
# -------------------------------------------------------------------------------
"""Models used by social search service"""
# -------------------------------------------------------------------------------
# Copyright (C) 2022 Array Insights, Inc. All Rights Reserved.
# Private and Confidential. Internal Use Only.
#     This software contains proprietary information which shall not
#     be reproduced or transferred to other documents and shall not
#     be disclosed to others for any purpose without
#     prior written permission of Array Insights, Inc.
# -------------------------------------------------------------------------------

from datetime import datetime
from enum import Enum
from typing import List, Optional
from xmlrpc.client import Boolean

from fastapi import HTTPException, status
from fastapi.encoders import jsonable_encoder
from pydantic import Field, StrictStr

from app.data.operations import DatabaseOperations
from app.models.common import PyObjectId, SailBaseModel


class PostState(Enum):
    IN_QUEUE = "IN QUEUE"
    REQUESTED = "REQUESTED"
    IN_PROGRESS = "IN PROGRESS"
    APPROVED = "APPROVED"
    DENIED = "DENIED"
    DELETED = "DELETED"


class SearchHistory_Base(SailBaseModel):
    user_id: PyObjectId = Field()
    organization_id: PyObjectId = Field()
    query: StrictStr = Field()
    social: StrictStr = Field(default="reddit")
    search_time: datetime = Field()
    after: Optional[StrictStr] = Field(default=None)


class SearchHistory_Db(SearchHistory_Base):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")


class SearchHistoryResponse(SailBaseModel):
    query: StrictStr = Field()
    social: StrictStr = Field(default="reddit")
    search_time: datetime = Field()
    after: Optional[StrictStr] = Field(default=None)
    user_name: StrictStr = Field()
    job_title: StrictStr = Field()


class RedditPost(SailBaseModel):
    reddit_id: StrictStr = Field()
    name: StrictStr = Field()
    link: StrictStr = Field()
    author: StrictStr = Field()
    author_link: StrictStr = Field()
    title: StrictStr = Field()
    subreddit: StrictStr = Field()
    selftext: Optional[StrictStr] = Field(default=None)
    images: List[StrictStr] = Field()
    post_time: datetime = Field()
    created_utc: int = Field()
    is_patient_story: Optional[Boolean] = Field(default=None)


class RedditPost_Db(RedditPost):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    organization_id: PyObjectId = Field()
    status: PostState = Field(default=PostState.REQUESTED)
    added_time: datetime = Field(default_factory=datetime.utcnow)
    added_by: PyObjectId = Field()
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    contact_method: Optional[StrictStr] = Field(default=None)
    contacted_at: Optional[datetime] = Field(default=None)
    contacted_by: Optional[StrictStr] = Field(default=None)


class PostTagResponse(SailBaseModel):
    id: PyObjectId = Field()
    social: StrictStr = Field(default="reddit")
    post: RedditPost = Field()
    status: PostState = Field()
    added_time: datetime = Field()
    user_name: StrictStr = Field()
    job_title: StrictStr = Field()
    contact_method: Optional[StrictStr] = Field(default=None)
    contacted_at: Optional[datetime] = Field(default=None)
    contacted_by: Optional[StrictStr] = Field(default=None)


class PostTagUpdate(SailBaseModel):
    status: Optional[PostState] = Field(default=None)
    contact_method: Optional[StrictStr] = Field(default=None)
    contacted_at: Optional[datetime] = Field(default=None)
    contacted_by: Optional[StrictStr] = Field(default=None)


class SearchHistory:
    DB_COLLECTION_SEARCH_HISTORY = "search_history"
    data_service = DatabaseOperations()

    @staticmethod
    async def create(
        search: SearchHistory_Db,
    ):
        return await SearchHistory.data_service.insert_one(
            collection=SearchHistory.DB_COLLECTION_SEARCH_HISTORY,
            data=jsonable_encoder(search),
        )

    @staticmethod
    async def read(
        organization_id: Optional[PyObjectId] = None,
        user_id: Optional[PyObjectId] = None,
        skip: Optional[int] = None,
        limit: Optional[int] = None,
        sort_key: str = "search_time",
        sort_direction: int = -1,
        throw_on_not_found: bool = True,
    ) -> List[SearchHistory_Db]:
        search_list = []

        query = {}
        if user_id:
            query["user_id"] = str(user_id)
        if organization_id:
            query["organization_id"] = str(organization_id)

        if skip is None and limit is None:
            response = await SearchHistory.data_service.find_by_query(
                collection=SearchHistory.DB_COLLECTION_SEARCH_HISTORY,
                query=jsonable_encoder(query),
            )
        elif skip is not None and limit is not None:
            response = await SearchHistory.data_service.find_sorted_pagination(
                collection=SearchHistory.DB_COLLECTION_SEARCH_HISTORY,
                query=jsonable_encoder(query),
                sort_key=sort_key,
                sort_direction=sort_direction,
                skip=skip,
                limit=limit,
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Both skip and limit need to be provided for pagination",
            )

        if response:
            for search in response:
                search_list.append(SearchHistory_Db(**search))
        elif throw_on_not_found:
            raise HTTPException(status_code=404, detail="Search history not found")

        return search_list


class RedditPosts:
    DB_COLLECTION_REDDIT_POSTS = "reddit_posts"
    data_service = DatabaseOperations()

    @staticmethod
    async def create(
        post: RedditPost_Db,
    ):
        return await RedditPosts.data_service.insert_one(
            collection=RedditPosts.DB_COLLECTION_REDDIT_POSTS,
            data=jsonable_encoder(post),
        )

    @staticmethod
    async def read(
        organization_id: Optional[PyObjectId] = None,
        user_id: Optional[PyObjectId] = None,
        post_id: Optional[PyObjectId] = None,
        skip: Optional[int] = None,
        limit: Optional[int] = None,
        sort_key: str = "added_time",
        sort_direction: int = -1,
        throw_on_not_found: bool = True,
    ) -> List[RedditPost_Db]:
        posts_list = []

        query = {}
        if post_id:
            query["_id"] = str(post_id)
        if user_id:
            query["user_id"] = str(user_id)
        if organization_id:
            query["organization_id"] = str(organization_id)
        query["status"] = {"$ne": PostState.DELETED.value}

        if skip is None and limit is None:
            response = await RedditPosts.data_service.find_by_query(
                collection=RedditPosts.DB_COLLECTION_REDDIT_POSTS,
                query=jsonable_encoder(query),
            )
        elif skip is not None and limit is not None:
            response = await RedditPosts.data_service.find_sorted_pagination(
                collection=RedditPosts.DB_COLLECTION_REDDIT_POSTS,
                query=jsonable_encoder(query),
                sort_key=sort_key,
                sort_direction=sort_direction,
                skip=skip,
                limit=limit,
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Both skip and limit need to be provided for pagination",
            )

        if response:
            for post in response:
                posts_list.append(RedditPost_Db(**post))
        elif throw_on_not_found:
            raise HTTPException(status_code=404, detail="Reddit Post not found")

        return posts_list

    @staticmethod
    async def update(
        organization_id: PyObjectId,
        post_id: PyObjectId,
        status: Optional[PostState] = None,
        contact_method: Optional[StrictStr] = None,
        contacted_by: Optional[StrictStr] = None,
        contacted_at: Optional[datetime] = None,
    ):
        update_request = {"$set": {}}
        if status:
            update_request["$set"]["status"] = status.value
        if contact_method:
            update_request["$set"]["contact_method"] = contact_method
        if contacted_by:
            update_request["$set"]["contacted_by"] = contacted_by
        if contacted_at:
            update_request["$set"]["contacted_at"] = contacted_at

        update_request["$set"]["updated_at"] = datetime.utcnow()

        return await RedditPosts.data_service.update_one(
            collection=RedditPosts.DB_COLLECTION_REDDIT_POSTS,
            query={"_id": str(post_id), "organization_id": str(organization_id)},
            data=jsonable_encoder(update_request),
        )
