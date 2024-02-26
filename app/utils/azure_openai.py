from typing import Dict, List

import openai


class OpenAiGenerator:
    def __new__(cls, api_base, api_key) -> "OpenAiGenerator":
        if not hasattr(cls, "instance"):
            openai.api_type = "azure"
            openai.api_version = "2023-07-01-preview"
            openai.api_base = api_base
            openai.api_key = api_key
            cls.engine = "paggpt4"
            cls.instance = super(OpenAiGenerator, cls).__new__(cls)
        return cls.instance

    async def get_response(self, messages: List[Dict]) -> str:
        response = await openai.ChatCompletion.acreate(
            engine=self.engine,
            messages=messages,
            temperature=0.7,
            max_tokens=800,
            top_p=0.95,
            frequency_penalty=0,
            presence_penalty=0,
            stop=None,
        )

        if not hasattr(response, "choices"):
            raise Exception("No response from OpenAI. Response: ", response)

        return response.choices[0].message["content"]  # type: ignore
