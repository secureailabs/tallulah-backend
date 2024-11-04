from typing import Any, Dict, List, Optional, Union

from openai import NOT_GIVEN, AsyncAzureOpenAI
from pydantic import BaseModel


class OpenAiGenerator:
    def __new__(cls, api_base, api_key) -> "OpenAiGenerator":
        if not hasattr(cls, "instance"):
            cls.client = AsyncAzureOpenAI(azure_endpoint=api_base, api_key=api_key, api_version="2024-10-21")
            cls.model = "gpt-4o"
            cls.instance = super(OpenAiGenerator, cls).__new__(cls)
        return cls.instance

    async def get_response(
        self,
        messages: List[Dict],
        response_model: Optional[type[BaseModel]] = None,
    ) -> Union[str, Any]:
        response = await self.client.beta.chat.completions.parse(
            model=self.model,
            messages=messages,  # type: ignore
            stop=NOT_GIVEN,
            response_format=response_model if response_model else NOT_GIVEN,
        )

        if not hasattr(response.choices[0], "message"):
            raise Exception("No response from OpenAI. Response: ", response)
        if not hasattr(response.choices[0].message, "content"):
            raise Exception("No content in OpenAI response. Response: ", response)
        if not response_model and not response.choices[0].message.content:
            raise Exception("Empty content in OpenAI response. Response: ", response)

        if response_model:
            if response.choices[0].message.parsed:
                return response.choices[0].message.parsed
            else:
                return response.choices[0].message.refusal
        else:
            return response.choices[0].message.content

    async def generate_transcript(self, audio_path: str) -> str:
        with open(audio_path, "rb") as audio_file:
            response = await self.client.audio.transcriptions.create(
                model="whisper",
                file=audio_file,
            )

            if not hasattr(response, "text"):
                raise Exception("No transcription from OpenAI. Response: ", response)

            return response.text

    async def describe_image(self, image_url: str) -> str:
        prompt = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Describe the image."},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": image_url,
                        },
                    },
                ],
            }
        ]

        return await self.get_response(prompt)


# test the OpenAiGenerator
async def test_openai_generator():
    import os

    openai_generator = OpenAiGenerator(os.getenv("OPENAI_API_BASE"), os.getenv("OPENAI_API_KEY"))
    response = await openai_generator.get_response(
        [
            {
                "role": "system",
                "content": "You are an AI assistant that works with the United Mitochondrial Disease Foundation (UMDF).",
            },
            {"role": "user", "content": "What do you do?"},
        ]
    )
    print(response)


if __name__ == "__main__":
    import asyncio

    asyncio.run(test_openai_generator())
