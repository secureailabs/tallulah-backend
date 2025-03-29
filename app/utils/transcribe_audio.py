# -------------------------------------------------------------------------------
# Engineering
# transcribe_audio.py
# -------------------------------------------------------------------------------
""" Service to transcribe audio files """
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

from app.models.common import PyObjectId
from app.utils.azure_blob_manager import AzureBlobManager
from app.utils.azure_openai import OpenAiGenerator
from app.utils.secrets import secret_store
from app.utils.shell_process import run_shell_code


async def transcribe_audio(audio_path: str) -> str:

    audio_files = [audio_path]
    try:
        # if the size of the audio file is more than 25MB, split it into 25MB chunk audio files
        audio_size = os.path.getsize(audio_path)
        if audio_size > 25 * 1024 * 1024:
            audio_files = []
            chunk_size = 25 * 1024 * 1024
            chunk_count = audio_size // chunk_size + 1
            for i in range(chunk_count):
                chunk_audio_path = f"{audio_path}_{i}.wav"
                cmd = f'ffmpeg -y -i "{audio_path}" -ss {i * chunk_size} -t {chunk_size} {chunk_audio_path}'
                split_op_status = await run_shell_code(cmd)
                if split_op_status.status != 0:
                    raise Exception(f"ffmpeg failed: {split_op_status.error}")
                audio_files.append(chunk_audio_path)

        openai_generator = OpenAiGenerator(api_base=secret_store.OPENAI_API_BASE, api_key=secret_store.OPENAI_API_KEY)

        transcript = ""
        for audio_file in audio_files:
            transcript += await openai_generator.generate_transcript(audio_file)
    except Exception as e:
        raise Exception(f"Transcription failed: {str(e)}")
    finally:
        # remove only the chunk audio files as they were created in this function
        if len(audio_files) > 1:
            for audio_file in audio_files:
                os.remove(audio_file)

    return transcript


async def transcribe_audio_from_id(audio_id: PyObjectId, file_name: str) -> str:
    # clean file_name
    file_name = file_name.replace(" ", "_").replace(":", "_").replace("/", "_").replace("\\", "_")
    storage_manager = AzureBlobManager(secret_store.STORAGE_ACCOUNT_CONNECTION_STRING, "form-audio")
    audio_file_data = await storage_manager.download_blob(str(audio_id))

    # write the audio file data to file async
    audio_file_name = str(audio_id) + file_name
    async with aiofiles.open(audio_file_name, "wb") as f:
        await f.write(audio_file_data)

    try:
        transcript = await transcribe_audio(audio_file_name)
    except Exception as e:
        raise Exception(f"Transcription failed: {str(e)}")
    finally:
        # remove the audio file
        os.remove(audio_file_name)

    return transcript
