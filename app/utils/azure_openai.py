from typing import Dict, List

from openai import AsyncAzureOpenAI


class OpenAiGenerator:
    def __new__(cls, api_base, api_key) -> "OpenAiGenerator":
        if not hasattr(cls, "instance"):
            cls.client = AsyncAzureOpenAI(azure_endpoint=api_base, api_key=api_key, api_version="2024-02-01")
            cls.model = "paggpt4"
            cls.instance = super(OpenAiGenerator, cls).__new__(cls)
        return cls.instance

    async def get_response(self, messages: List[Dict]) -> str | None:

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.7,
            max_tokens=800,
            top_p=0.95,
            frequency_penalty=0,
            presence_penalty=0,
            stop=None,
        )

        if not hasattr(response.choices[0], "message"):
            raise Exception("No response from OpenAI. Response: ", response)
        if not hasattr(response.choices[0].message, "content"):
            raise Exception("No content in OpenAI response. Response: ", response)

        return response.choices[0].message.content


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
