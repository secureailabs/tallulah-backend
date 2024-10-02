import json
from typing import Dict

from app.models.common import PyObjectId
from app.models.content_generation_template import Context
from app.models.form_data import AudioMetadata, FormDataMetadata, FormDatas, ImageMetadata, VideoMetadata
from app.utils.azure_openai import OpenAiGenerator
from app.utils.lock_store import LocalLockStore
from app.utils.message_queue import InMemoryProducerConsumer, MessageQueueTypes
from app.utils.secrets import secret_store
from app.utils.transcribe_audio import transcribe_audio_from_id
from app.utils.transcribe_image import describe_image_from_id
from app.utils.transcribe_video import transcribe_video_from_id


async def generate_structured_data(metadata: FormDataMetadata, form_values: Dict) -> Dict:
    system_message = """
    Extract the following information from the provided text, which may include data from forms or transcriptions of images, videos, or audio attachments. The text might be unstructured or conversational.
    Information to extract:
    - Name
    - Age
    - Location
    - Diagnosis
    - Events (list any significant events mentioned)
    - Date of event
    - Emotion of event
    - Overall theme or basic concerns related to the disease

    Present the extracted information in JSON format, using the following structure:

    ```json
    {
    "Name": "",
    "Age": "",
    "Location": "",
    "Diagnosis": "",
    "Events": "",
    "Date of Event": "",
    "Emotion of Event": "",
    "Overall Theme or Basic Concerns": ""
    }
    ```
"""

    # prepare prompts for OpenAI
    system_prompt = Context(
        role="system",
        content=system_message,
    )
    all_data = str(form_values)
    for video in metadata.video_metadata:
        all_data += "Video ID: " + str(video.video_id) + ":\n" + video.transcript + "\n"
    for image in metadata.image_metadata:
        all_data += "Image ID: " + str(image.image_id) + ":\n" + image.transcript + "\n"
    for audio in metadata.audio_metadata:
        all_data += "Audio ID: " + str(audio.audio_id) + ":\n" + audio.transcript + "\n"

    user_prompt = Context(role="user", content=all_data)
    conversation = [system_prompt, user_prompt]
    conversation = [message.model_dump() for message in conversation]

    # generate structured data
    openai_generator = OpenAiGenerator(api_base=secret_store.OPENAI_API_BASE, api_key=secret_store.OPENAI_API_KEY)
    structured_data = await openai_generator.get_response(conversation)

    # Extract the data between opening and closing ```json
    structured_data = structured_data.split("```json")[1].split("```")[0].strip()

    # TODO: Parse the structured data and return it
    return json.loads(structured_data)


async def on_generate_structured_data(form_data_id: str):
    # acquire the lock on the form data for 10minutes to prevent multiple processing
    # if lock acquisition fails, return
    # i

    lock_store = LocalLockStore()
    acquire_lock = lock_store.acquire(f"form_data_{form_data_id}", expiry=60 * 10)
    if not acquire_lock:
        return

    # fetch the form data
    form_data = await FormDatas.read(form_data_id=PyObjectId(form_data_id))
    form_data = form_data[0]

    # Get list of all the audio, video and image that are already transcribed
    transcribed_video = {}
    transcribed_audio = {}
    transcribed_image = {}
    if form_data.metadata:
        transcribed_video = {video.video_id: video for video in form_data.metadata.video_metadata}
        transcribed_audio = {audio.audio_id: audio for audio in form_data.metadata.audio_metadata}
        transcribed_image = {image.image_id: image for image in form_data.metadata.image_metadata}

    # Generate metadata for audio, video and image that are not transcribed
    form_metadata = FormDataMetadata()
    user_provided_data = {}
    for data in form_data.values:
        if form_data.values[data]["type"] == "VIDEO":
            for video in form_data.values[data]["value"]:
                video_id = PyObjectId(video["id"])
                if video_id in transcribed_video and form_data.metadata:
                    form_metadata.video_metadata.append(transcribed_video[video_id])
                    continue
                video_transcript = await transcribe_video_from_id(video_id, video["name"])
                form_metadata.video_metadata.append(VideoMetadata(video_id=video_id, transcript=video_transcript))

        elif form_data.values[data]["type"] == "IMAGE":
            for image in form_data.values[data]["value"]:
                image_id = PyObjectId(image["id"])
                if image_id in transcribed_image:
                    form_metadata.image_metadata.append(transcribed_image[image_id])
                    continue
                image_description = await describe_image_from_id(image_id)
                form_metadata.image_metadata.append(ImageMetadata(image_id=image_id, transcript=image_description))

        elif form_data.values[data]["type"] == "AUDIO":
            for audio in form_data.values[data]["value"]:
                audio_id = PyObjectId(audio["id"])
                if audio_id in transcribed_audio:
                    form_metadata.audio_metadata.append(transcribed_audio[audio_id])
                    continue
                audio_transcript = await transcribe_audio_from_id(audio_id, audio["name"])
                form_metadata.audio_metadata.append(AudioMetadata(audio_id=audio_id, transcript=audio_transcript))

        else:
            user_provided_data[data] = form_data.values[data]["value"]

    # After the audio, video and image metadata is generated, we can extract the structured data
    structured_data = await generate_structured_data(form_metadata, user_provided_data)
    form_metadata.structured_data = structured_data

    # Update the database
    await FormDatas.update(query_form_data_id=PyObjectId(form_data_id), update_form_data_metadata=form_metadata)

    # Release the lock
    lock_store.release(f"form_data_{form_data_id}")


async def generate_structured_data_consumer():
    # Structured data generation is done via a message queue to avoid hitting the OpenAI API rate limit
    # Since all the messages will be consumed in order, we can be sure that the rate limit will not be hit
    task_queue = InMemoryProducerConsumer(
        queue_name=MessageQueueTypes.FORM_DATA_METADATA_GENERATION, connection_string=""
    )
    await task_queue.connect()
    await task_queue.consume_messages(on_generate_structured_data)
