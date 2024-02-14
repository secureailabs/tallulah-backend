# -------------------------------------------------------------------------------
# Tallulah
# main.py
# -------------------------------------------------------------------------------
"""The main entrypoint of the Tallulah Services"""
# -------------------------------------------------------------------------------
# Copyright (C) 2022 Array Insights, Inc. All Rights Reserved.
# Private and Confidential. Internal Use Only.
#     This software contains proprietary information which shall not
#     be reproduced or transferred to other documents and shall not
#     be disclosed to others for any purpose without
#     prior written permission of Array Insights, Inc.
# -------------------------------------------------------------------------------

import base64
import json
import logging
import time
import traceback
from typing import Any, Callable, Dict, List, Union
from urllib.parse import parse_qs, urlencode

import aiohttp
import fastapi.openapi.utils as utils
from fastapi import FastAPI, Response, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.requests import Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi_responses import custom_openapi
from pydantic import BaseModel, Field, StrictStr

from app.api import (
    accounts,
    authentication,
    content_generation,
    content_generation_template,
    emails,
    form_data,
    form_templates,
    internal_utils,
    mailbox,
    response_templates,
)
from app.data.operations import DatabaseOperations
from app.models.common import PyObjectId
from app.utils.elastic_search import ElasticsearchClient
from app.utils.log_manager import LogLevel, add_log_message
from app.utils.secrets import secret_store

server = FastAPI(
    title="Tallulah",
    description="All the private and public APIs for Tallulah - Patient Story Management Platform",
    version="0.1.0",
    openapi_url="/api/openapi.json",
    docs_url=None,
)
server.openapi = custom_openapi(server)


# Add all the API services here exposed to the public
server.include_router(authentication.router)
server.include_router(accounts.router)
server.include_router(internal_utils.router)
server.include_router(mailbox.router)
server.include_router(emails.router)
server.include_router(response_templates.router)
server.include_router(form_templates.router)
server.include_router(form_data.router)
server.include_router(content_generation_template.router)
server.include_router(content_generation.router)

# Setup CORS to allow all origins
origins = [
    "*",
]
server.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
server.add_middleware(GZipMiddleware, minimum_size=1000)


# Initialize the elasticsearch client
elasticsearch_client = ElasticsearchClient(
    cloud_id=secret_store.ELASTIC_CLOUD_ID,
    password=secret_store.ELASTIC_PASSWORD,
)


# Override the default validation error handler as it throws away a lot of information
# about the schema of the request body.
class ValidationError(BaseModel):
    error: StrictStr = Field(default="Invalid Schema")


@server.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    error = ValidationError(error="Invalid Schema")
    return JSONResponse(status_code=422, content=jsonable_encoder(error))


utils.validation_error_response_definition = ValidationError.schema()


# Record all the exceptions that are not handled by the API and send them to slack and the database
@server.exception_handler(Exception)
async def server_error_exception_handler(request: Request, exc: Exception):
    message = {
        "_id": str(PyObjectId()),
        "exception": f"{str(exc)}",
        "request": f"{request.method} {request.url}",
        "stack_trace": f"{traceback.format_exc()}",
    }

    # if the slack webhook is set, send the error to slack via aiohttp
    if secret_store.SLACK_WEBHOOK:
        headers = {"Content-type": "application/json"}
        async with aiohttp.ClientSession() as session:
            async with session.post(
                secret_store.SLACK_WEBHOOK,
                headers=headers,
                json={
                    "text": json.dumps(
                        {
                            "id": message["_id"],
                            "exception": message["exception"],
                        },
                        indent=2,
                    )
                },
            ) as response:
                logging.info(f"Slack webhook response: {response.status}")

    # Add it to the sail database audit log
    data_service = DatabaseOperations()
    await data_service.insert_one("errors", jsonable_encoder(message))

    # Add the exception to the audit log as well
    add_log_message(LogLevel.ERROR, message)

    # Respond with a 500 error
    return Response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content="Internal Server Error id: {}".format(message["_id"]),
    )


# Serve the Swagger UI on the /docs route and use the pre-downloaded js and css files
@server.get("/api/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    if server.openapi_url is None:
        raise RequestValidationError("openapi_url must be provided to serve Swagger UI")

    server.mount("/api/static", StaticFiles(directory="./app/static"), name="static")
    return get_swagger_ui_html(
        openapi_url=server.openapi_url,
        title=server.title + " - Swagger UI",
        oauth2_redirect_url=server.swagger_ui_oauth2_redirect_url,
        swagger_js_url="/api/static/swagger-ui-bundle.js",
        swagger_css_url="/api/static/swagger-ui.css",
    )


@server.get("/", include_in_schema=False)
async def health_probe():
    return Response(status_code=status.HTTP_200_OK)


async def set_body(request: Request, body: bytes):
    async def receive():
        return {"type": "http.request", "body": body}

    request._receive = receive


async def get_body(request: Request) -> bytes:
    body = await request.body()
    await set_body(request, body)
    return body


def remove_sensitive_info(request_body: Union[Dict, List, Any]):
    if isinstance(request_body, Dict):
        for key in request_body.keys():
            if "password" in key:
                request_body[key] = "****"
            elif isinstance(request_body[key], dict):
                request_body[key] = remove_sensitive_info(request_body[key])
        return request_body
    elif isinstance(request_body, List):
        for i in range(len(request_body)):
            request_body[i] = remove_sensitive_info(request_body[i])
        return request_body
    else:
        return request_body


@server.middleware("http")
async def add_audit_log(request: Request, call_next: Callable):
    await set_body(request, await request.body())
    request_body = await get_body(request)

    # remove sensitive data from the request body
    if "Content-Type" in request.headers:
        if request.headers.get("Content-Type") == "application/json":
            request_body = json.loads(request_body)
            # recursively remove password from the request body
            request_body_json = remove_sensitive_info(request_body)
            request_body = json.dumps(request_body_json)
        elif request.headers.get("Content-Type") == "application/x-www-form-urlencoded":
            request_body = parse_qs(request_body.decode("utf-8"))
            if "password" in request_body:
                request_body["password"][0] = "****"
            request_body = urlencode(request_body, doseq=True)

    # calculate the response time
    start_time = time.time()
    response: Response = await call_next(request)
    process_time = (time.time() - start_time) * 1000
    response.headers["X-Process-Time"] = str(process_time) + "ms"

    # Extract the user id from the JWT token in the request header
    user_id = None
    if "Authorization" in request.headers:
        auth_token_list = request.headers["Authorization"].split(".")
        if len(auth_token_list) > 1:
            user_info_base_64 = request.headers["Authorization"].split(".")[1]
            user_info = json.loads(base64.b64decode(user_info_base_64 + "=="))
            user_id = user_info["_id"]

    message = {
        "user_id": user_id,
        "host": f"{request.client.host}",  # type: ignore
        "method": f"{request.method}",
        "url": f"{request.url.path}",
        "request_body": f"{request_body}",
        "response": response.status_code,
        "response_time": process_time,
    }

    add_log_message(LogLevel.INFO, message)

    return response
