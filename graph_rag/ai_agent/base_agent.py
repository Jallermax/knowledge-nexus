import openai
from graph_rag.config.config_manager import Config

class BaseAgent:
    def __init__(self):
        self.config = Config()
        openai.api_key = self.config.API_KEY
        self.model = self.config.LLM_MODEL
        self.temperature = self.config.LLM_TEMPERATURE
        self.max_tokens = self.config.LLM_MAX_TOKENS

    def generate_response(self, prompt):
        response = openai.ChatCompletion.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )
        return response.choices[0].message['content'].strip()
