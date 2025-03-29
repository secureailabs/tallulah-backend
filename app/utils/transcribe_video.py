# -------------------------------------------------------------------------------
# Engineering
# transcribe_video.py
# -------------------------------------------------------------------------------
""" Service to transcribe video files """
# -------------------------------------------------------------------------------
# Copyright (C) 2024 Array Insights, Inc. All Rights Reserved.
# Private and Confidential. Internal Use Only.
#     This software contains proprietary information which shall not
#     be reproduced or transferred to other documents and shall not
#     be disclosed to others for any purpose without
#     prior written permission of Array Insights, Inc.
# -------------------------------------------------------------------------------

import os

import aiofiles

from app.utils.azure_blob_manager import AzureBlobManager
from app.utils.secrets import secret_store
from app.utils.shell_process import run_shell_code
from app.utils.transcribe_audio import transcribe_audio


async def transcribe_video(video_path: str) -> str:
    audio_path = video_path + ".wav"
    cmd = f'ffmpeg -y -i "{video_path}" -vn -acodec pcm_s16le -ar 16000 -ac 1 "{audio_path}"'
    extraction_result = await run_shell_code(cmd)
    if extraction_result.status != 0:
        raise Exception(f"ffmpeg failed: {extraction_result.error}")

    transcription = await transcribe_audio(audio_path)

    # remove the audio file
    os.remove(audio_path)

    return transcription


async def transcribe_video_from_id(video_id, file_name) -> str:
    # clean file_name
    file_name = file_name.replace(" ", "_").replace(":", "_").replace("/", "_").replace("\\", "_")
    storage_manager = AzureBlobManager(secret_store.STORAGE_ACCOUNT_CONNECTION_STRING, "form-video")
    video_file_data = await storage_manager.download_blob(str(video_id))

    # write the video file data to file async
    video_file_name = str(video_id) + file_name
    async with aiofiles.open(video_file_name, "wb") as f:
        await f.write(video_file_data)

    video_transcription = await transcribe_video(video_file_name)

    # remove the video file
    os.remove(video_file_name)

    return video_transcription
