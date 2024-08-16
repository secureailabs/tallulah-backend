# -------------------------------------------------------------------------------
# Engineering
# organization.py
# -------------------------------------------------------------------------------
"""APIs used for Organizations"""
# -------------------------------------------------------------------------------
# Copyright (C) 2024 Array Insights, Inc. All Rights Reserved.
# Private and Confidential. Internal Use Only.
#     This software contains proprietary information which shall not
#     be reproduced or transferred to other documents and shall not
#     be disclosed to others for any purpose without
#     prior written permission of Array Insights, Inc.
# -------------------------------------------------------------------------------

from datetime import datetime
from typing import List, Optional
from collections.abc import Iterable

from app.models.form_templates import FormTemplate_Db, FormTemplates
from fastapi import BackgroundTasks, APIRouter, Body, Depends, HTTPException, Path, Query, Response, status
from fastapi_utils.tasks import repeat_every
from fastapi.encoders import jsonable_encoder
from fastapi.concurrency import run_in_threadpool

from app.api.authentication import get_current_user
from app.models.authentication import TokenData
from app.models.common import PyObjectId
from app.models.form_data import FormDatas
from app.models.organizations import (
    ExportData_Db,
    ExportData_Out,
    DataExports,
    ExportState,
    ExportType,
)
from app.models.form_templates import (
    FormTemplatesData,
    FormTemplateData_Db,
    FormTemplateData_Base,
    FormTheme,
)
from app.models.form_templates import GetStorageUrl_Out
from app.models.content_generation_template import Context
from app.utils.azure_openai import OpenAiGenerator
from app.utils.secrets import secret_store
from collections import Counter
from app.data.operations import DatabaseOperations
from app.utils.azure_blob_manager import AzureBlobManager
import json
import os
import shutil
import csv

router = APIRouter(prefix="/api/organization", tags=["organization"])

async def aggregate_themes(template: FormTemplate_Db):
    skip = 0
    limit = 1000
    themes = {}
    while True:
        forms = await FormDatas.read(form_template_id=template.id, skip=skip, limit=limit, throw_on_not_found=False)
        if not forms or len(forms) == 0:
            break
        skip += limit
        for form in forms:
            if not form.themes or len(form.themes) == 0:
                continue
            for theme in form.themes:
                if theme not in themes:
                    themes[theme] = 0
                themes[theme] += 1

    themes = Counter(themes).most_common(10)

    db_themes = []
    for theme, c in themes:
        db_themes.append(FormTheme(theme=theme, count=c))

    old_data = await FormTemplatesData.get_template_data(template.id)
    if old_data:
        old_data.top_themes = db_themes
        await FormTemplatesData.update(old_data)
    else:
        await FormTemplatesData.create(FormTemplateData_Db(id=template.id, top_themes=db_themes))


async def write_export_data(basedir: str, filename: str, export_data: list):
    with open(basedir+"/"+filename, 'w') as file:
        await run_in_threadpool(lambda: json.dump(export_data, file))


async def export_all_data(request: ExportData_Db):
    request.status = ExportState.IN_PROGRESS
    await DataExports.update(request)

    ds = DatabaseOperations()
    basedir = f"/tmp/{str(request.id)}"
    os.makedirs(basedir, exist_ok=True)

    try:
        if request.export_type == ExportType.JSON:
            await export_as_json(basedir, ds, request)
        elif request.export_type == ExportType.CSV:
            await export_as_csv(basedir, ds, request)
    except Exception as e:
        # TODO: Log error
        # print(e)
        request.status = ExportState.FAILED
        await DataExports.update(request)
        return

    request.filename = f"{str(request.id)}.zip"
    request.status = ExportState.COMPLETED

    await run_in_threadpool(lambda: shutil.make_archive(basedir, 'zip', basedir))
    shutil.rmtree(basedir)

    storage_manager = AzureBlobManager(
        secret_store.STORAGE_ACCOUNT_CONNECTION_STRING, "exports"
    )
    with open(basedir+".zip", "rb") as file:
        await storage_manager.upload_blob(request.filename, file.read())

    os.remove(basedir+".zip")
    await DataExports.update(request)


async def export_forms_csv(filename: str, ds: DatabaseOperations, request: ExportData_Db):
    templates = await ds.find_sorted_pagination(
        collection="form_templates",
        query=jsonable_encoder({
            "organization_id": request.organization_id,
        }),
        sort_key="_id",
        sort_direction=-1,
        skip=0,
        limit=1000, # Expecting only a max 1000 templates in an organization
    )
    if not templates or len(templates) == 0:
        return
    # TODO: Currently not exporting form templates

    # Export form_data
    page = 0
    for template in templates:
        skip = 0
        limit = 1000
        while True:
            data = await ds.find_sorted_pagination(
                collection="form_data",
                query=jsonable_encoder({
                    "form_template_id": {"$in": [template["_id"]]},
                }),
                sort_key="_id",
                sort_direction=-1,
                skip=skip,
                limit=limit,
            )
            if not data or len(data) == 0:
                break
            skip += limit
            page += 1

            # Write data to csv
            fullname = f"{filename}_{page}.csv"
            rows = []
            headers = ["id", "time", "state"]
            for form in data:
                row = {"id": form["_id"], "time": form["creation_time"], "state": form["state"] if "state" in form else ""}
                for k, v in form["values"].items():
                    if "value" in v:
                        v = v["value"]

                    if isinstance(v, str):
                        row[k] = v
                    elif isinstance(v, Iterable):
                        if len(v) <= 0:
                            row[k] = ""
                        elif isinstance(v[0], dict):
                            row[k] = v[0]["name"] if "name" in v[0] else "Unknown"
                        else:
                            row[k] = ";".join(v)
                    else:
                        row[k] = v
                    if k not in headers:
                        headers.append(k)
                rows.append(row)

            with open(fullname, 'w') as file:
                csvwriter = csv.DictWriter(file, fieldnames=headers)
                csvwriter.writeheader()
                csvwriter.writerows(rows)


async def export_as_csv(basedir: str, ds: DatabaseOperations, request: ExportData_Db):
    data_sets = {
        "forms": export_forms_csv,
    }

    for data, func in data_sets.items():
        filename = f"{basedir}/{data}"
        await func(filename, ds, request)


async def export_as_json(basedir: str, ds: DatabaseOperations, request: ExportData_Db):
    collections = {
        "form_templates": [("form_data", "form_template_id"), ("form_templates_data", "_id")],
        # "patient_profiles": [],
        # "patient-chat": [],
        # "users": [],
        # "dashboard-templates": [],
        # "content-generation-template": [],
        # "content-generation": [],
        # "media-metadata": [],
    }

    for collection in collections:
        child_collections = collections[collection]
        skip = 0
        limit = 1000 if len(child_collections) == 0 else 20
        page = 0

        while True:
            response = await ds.find_sorted_pagination(
                collection=collection,
                query=jsonable_encoder({
                    "organization_id": request.organization_id,
                }),
                sort_key="_id",
                sort_direction=-1,
                skip=skip,
                limit=limit,
            )
            if not response or len(response) == 0:
                break
            skip += limit
            page += 1

            # Write response
            await write_export_data(basedir, f"{collection}_{page}.json", response)

            # Process child collections
            for child_collection, key in child_collections:
                cskip = 0
                climit = 1000
                cpage = 0
                while True:
                    child_response = await ds.find_sorted_pagination(
                        collection=child_collection,
                        query=jsonable_encoder({
                            key: {"$in": [r["_id"] for r in response]},
                        }),
                        sort_key="_id",
                        sort_direction=-1,
                        skip=cskip,
                        limit=climit,
                    )
                    if not child_response or len(child_response) == 0:
                        break
                    cskip += climit
                    cpage += 1

                    # Write child_response
                    await write_export_data(basedir, f"{child_collection}_{page}_{cpage}.json", child_response)


@router.post(
    path="/themes/regenerate",
    description="Regenerate organization themes",
    status_code=status.HTTP_201_CREATED,
    response_model_by_alias=False,
    operation_id="regenerate_themes",
)
async def regenerate_themes(
    current_user: TokenData = Depends(get_current_user),
    background_tasks: BackgroundTasks = None,
) -> str:
    templates = await FormTemplates.read(organization_id=current_user.organization_id)
    if not templates:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No templates found for the organization",
        )

    for template in templates:
        # Generate Tags
        # await aggregate_themes(template)
        background_tasks.add_task(aggregate_themes, template)

    return str(len(templates))


@router.post(
    path="/export/{export_type}",
    description="Export organization data",
    status_code=status.HTTP_201_CREATED,
    response_model_by_alias=False,
    operation_id="export_organization_data",
)
async def export_organization_data(
    export_type: str = Path(description="Export Type - csv or json"),
    current_user: TokenData = Depends(get_current_user),
    background_tasks: BackgroundTasks = None,
) -> ExportData_Db:
    if export_type not in [item.value for item in ExportType]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid export type. Supported types are csv and json",
        )

    # TODO: Implement export_type = csv as well
    export_data = ExportData_Db(user_id=current_user.id, organization_id=current_user.organization_id, export_type=export_type)
    await DataExports.create(export_data)

    # await export_all_data(request=export_data)
    background_tasks.add_task(export_all_data, export_data)

    return export_data


@router.get(
    path="/export/{export_id}",
    description="Get export status",
    status_code=status.HTTP_200_OK,
    response_model=ExportData_Out,
    operation_id="get_export_status",
)
async def get_export_status(
    export_id: PyObjectId = Path(description="Export ID"),
    current_user: TokenData = Depends(get_current_user),
) -> ExportData_Out:
    export_data = await DataExports.read(export_id=export_id)
    export_data = export_data[0]
    if export_data.organization_id != current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Export not found",
        )

    return ExportData_Out(**export_data.dict())


@router.get(
    path="/export",
    description="Get list of all exports & status",
    status_code=status.HTTP_200_OK,
    response_model=List[ExportData_Out],
    operation_id="get_all_export_status",
)
async def get_all_export_status(
    current_user: TokenData = Depends(get_current_user),
) -> List[ExportData_Out]:
    export_data = await DataExports.read(organization_id=current_user.organization_id)

    return [ExportData_Out(**data.dict()) for data in export_data]


@router.get(
    path="/export/{export_id}/download",
    description="Get export status",
    status_code=status.HTTP_200_OK,
    response_model=GetStorageUrl_Out,
    operation_id="download_export",
)
async def download_export(
    export_id: PyObjectId = Path(description="Export ID"),
    current_user: TokenData = Depends(get_current_user),
) -> GetStorageUrl_Out:
    export_data = await DataExports.read(export_id=export_id)
    export_data = export_data[0]
    if export_data.organization_id != current_user.organization_id or export_data.status != ExportState.COMPLETED or not export_data.filename:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Export not found",
        )

    storage_manager = AzureBlobManager(
        secret_store.STORAGE_ACCOUNT_CONNECTION_STRING, "exports"
    )
    download_url = storage_manager.generate_read_sas(export_data.filename)

    return GetStorageUrl_Out(id=export_data.id, url=download_url)
