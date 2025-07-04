import os
from decimal import Overflow

from flask import current_app
from fontTools.ttLib.tables.ttProgram import instructions
from openai import OpenAI


class OpenAIClient:
    def __init__(self):
        self.client = OpenAI(
            # This is the default and can be omitted
            api_key=os.environ.get("OPENAI_API_KEY"),
        )

    def generate_chatgpt_response(self, model, instructions, prompt):

        response = self.client.responses.create(
            model=model,
            instructions=instructions,
            input=prompt,
        )

        return response.output_text
