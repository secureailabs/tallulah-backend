# -------------------------------------------------------------------------------
# Engineering
# social_search.py
# -------------------------------------------------------------------------------
"""APIs used for social search features"""
# -------------------------------------------------------------------------------
# Copyright (C) 2024 Array Insights, Inc. All Rights Reserved.
# Private and Confidential. Internal Use Only.
#     This software contains proprietary information which shall not
#     be reproduced or transferred to other documents and shall not
#     be disclosed to others for any purpose without
#     prior written permission of Array Insights, Inc.
# -------------------------------------------------------------------------------

import urllib.parse
from datetime import datetime
from typing import List, Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, Path, Query, Response, status
from fastapi.concurrency import run_in_threadpool
from fastapi.encoders import jsonable_encoder

from app.api.authentication import get_current_user
from app.models.authentication import TokenData
from app.models.common import PyObjectId
from app.models.social_search import PostState, RedditPost, RedditPost_Db, RedditPosts, SearchHistory, SearchHistory_Db
from app.utils.azure_openai import OpenAiGenerator
from app.utils.secrets import secret_store

router = APIRouter(prefix="/api/social/search", tags=["social-search"])

MAX_REDDIT_POSTS = 30
FILTER_BATCH_SIZE = 30


def chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i : i + n]


async def filter_posts_by_patient_stories(posts: List[RedditPost]) -> List[RedditPost]:
    filtered_posts: List[RedditPost] = []
    messages = []
    messages.append(
        {
            "role": "system",
            "content": """
    You are an assistant who helps with reading reddit posts and finding which posts are posts by potential or current patients.
    Each story has an id, title, and optional selftext. Return comma separated ids of potential stories.
    """,
        }
    )
    ids = []
    for subposts in chunks(posts, FILTER_BATCH_SIZE):
        for post in subposts:
            messages.append(
                {
                    "role": "user",
                    "content": (
                        "id: " + post.reddit_id + ", title: " + post.title + (", selftext: " + post.selftext)
                        if post.selftext
                        else ""
                    ),
                }
            )
        openai = OpenAiGenerator(secret_store.OPENAI_API_BASE, secret_store.OPENAI_API_KEY)
        generated_content = await openai.get_response(messages=messages)
        ids.extend([x.strip() for x in generated_content.split(",")])

    for post in posts:
        if post.reddit_id in ids:
            post.is_patient_story = True
        filtered_posts.append(post)

    return filtered_posts


@router.get(
    path="/history",
    description="Search History",
    status_code=status.HTTP_200_OK,
    response_model_by_alias=False,
    operation_id="search_history",
)
async def search_history(
    current_user: TokenData = Depends(get_current_user),
    sort_key: str = Query(default="search_time", description="Sort key"),
    sort_direction: int = Query(default=-1, description="Sort direction"),
    skip: int = Query(default=0, description="Number of form data to skip"),
    limit: int = Query(default=10, description="Number of form data to return"),
) -> List[SearchHistory_Db]:
    result = []

    result = await SearchHistory.read(
        organization_id=current_user.organization_id,
        skip=skip,
        limit=limit,
        sort_key=sort_key,
        sort_direction=sort_direction,
    )
    return result


@router.get(
    path="/reddit",
    description="Reddit Search",
    status_code=status.HTTP_200_OK,
    response_model_by_alias=False,
    operation_id="reddit_search",
)
async def reddit_search(
    query: str = Query(description="Search query"),
    filter_patient_stories: bool = Query(default=True, description="Filter patient stories"),
    after: Optional[str] = Query(default=None, description="Page after, use value from name field"),
    current_user: TokenData = Depends(get_current_user),
) -> List[RedditPost]:
    result = []

    if not query:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query is required",
        )

    # Add search history
    await SearchHistory.create(
        SearchHistory_Db(
            user_id=current_user.id,
            organization_id=current_user.organization_id,
            query=query,
            social="reddit",
            search_time=datetime.utcnow(),
            after=after,
        )
    )
    url = f"https://oauth.reddit.com/search.json?limit={MAX_REDDIT_POSTS}&sort=new"
    if after:
        url += f"&after={after}"
    url += "&q=" + urllib.parse.quote(query)

    results = []
    async with httpx.AsyncClient() as client:
        response = await client.get(
            url,
            auth=(secret_store.REDDIT_API_KEY, secret_store.REDDIT_API_SECRET),
        )
        results = response.json()

    if "data" not in results or "children" not in results["data"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No results found",
        )

    for post in results["data"]["children"]:
        data = post["data"]
        images = []
        if "preview" in data:
            images = list(map(lambda x: x["source"]["url"], data["preview"]["images"]))
        result.append(
            RedditPost(
                reddit_id=data["id"],
                name=data["name"],
                link=data["url"],
                author=data["author"],
                author_link=f"https://www.reddit.com/user/{data['author']}",
                title=data["title"],
                subreddit=data["subreddit"],
                selftext=data["selftext"],
                images=images,
                post_time=data["created_utc"],
                is_patient_story=False,
            )
        )

    return await filter_posts_by_patient_stories(result) if filter_patient_stories else result


@router.get(
    path="/reddit/tags",
    description="Reddit Tagged Posts",
    status_code=status.HTTP_200_OK,
    response_model_by_alias=False,
    operation_id="reddit_tags",
)
async def reddit_tags(
    current_user: TokenData = Depends(get_current_user),
    user_id: Optional[PyObjectId] = Query(default=None, description="User ID"),
    sort_key: str = Query(default="added_time", description="Sort key"),
    sort_direction: int = Query(default=-1, description="Sort direction"),
    skip: int = Query(default=0, description="Number of form data to skip"),
    limit: int = Query(default=10, description="Number of form data to return"),
) -> List[RedditPost_Db]:
    result = []

    result = await RedditPosts.read(
        organization_id=current_user.organization_id,
        user_id=user_id,
        skip=skip,
        limit=limit,
        sort_key=sort_key,
        sort_direction=sort_direction,
    )
    return result


@router.post(
    path="/reddit/tags",
    description="Reddit Tagged Posts",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model_by_alias=False,
    operation_id="reddit_add_tag",
)
async def reddit_add_tag(
    reddit_post: RedditPost,
    current_user: TokenData = Depends(get_current_user),
) -> Response:
    post = RedditPost_Db(
        reddit_id=reddit_post.reddit_id,
        name=reddit_post.name,
        link=reddit_post.link,
        author=reddit_post.author,
        author_link=reddit_post.author_link,
        title=reddit_post.title,
        subreddit=reddit_post.subreddit,
        selftext=reddit_post.selftext,
        images=reddit_post.images,
        post_time=reddit_post.post_time,
        is_patient_story=reddit_post.is_patient_story,
        added_by=current_user.id,
        organization_id=current_user.organization_id,
        status=PostState.REQUESTED,
    )

    await RedditPosts.create(post)

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.put(
    path="/reddit/tags/{post_id}",
    description="Reddit Tagged Post Status Update",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model_by_alias=False,
    operation_id="reddit_update_tag_status",
)
async def reddit_update_tag_status(
    post_id: PyObjectId = Path(description="Post ID"),
    post_status: PostState = Query(description="Post status"),
    current_user: TokenData = Depends(get_current_user),
) -> Response:
    await RedditPosts.update_status(
        organization_id=current_user.organization_id,
        post_id=post_id,
        status=post_status,
    )

    return Response(status_code=status.HTTP_204_NO_CONTENT)