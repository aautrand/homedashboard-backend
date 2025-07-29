import json

from dashboard.src.ai.prompts import math_problem_generator_prompt

class MathAgent:
    def __init__(self, client):
        self.client = client

    def generate_problems(self, prompt):
        raw_problems = (
            self.client.generate_chatgpt_response("gpt-4o", math_problem_generator_prompt, prompt)
            .replace("json", "")
            .replace("```", "")
        )

        # TODO if its not valid json send it to get fixed.
        json_problems = json.loads(raw_problems)

        return json_problems