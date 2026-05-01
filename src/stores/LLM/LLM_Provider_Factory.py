from LLM_Enums import LLM_Enums
from providers.OPENAI_Provider import OPENAI_Provider
from providers.Cohere_Provider import Cohere_Provider
from helpers import Settings


class LLM_Provider_Factory:
    def __init__(self, config: Settings):
        self.config = config

    def create_provider(self, provider_name: str):
        if provider_name == LLM_Enums.OPENAI.value:
            return OPENAI_Provider(
                api_key=self.config.OPENAI_API_KEY,
                model_name=self.config.GENERATION_MODEL_NAME,
                api_url = self.config.OPENAI_API_URL,
                default_input_max_tokens=self.config.INPUT_DEFAULT_MAX_CHARACTERS,
                default_output_max_tokens=self.config.GENERATION_DEFAULT_MAX_TOKENS,
                default_temperature=self.config.GENERATION_DEFAULT_TEMPERATURE,
            )
        if provider_name == LLM_Enums.COHERE.value:
            return Cohere_Provider(
                api_key=self.config.COHERE_API_KEY,
                model_name=self.config.GENERATION_MODEL_NAME,
                default_input_max_tokens=self.config.INPUT_DEFAULT_MAX_CHARACTERS,
                default_output_max_tokens=self.config.GENERATION_DEFAULT_MAX_TOKENS,
                default_temperature=self.config.GENERATION_DEFAULT_TEMPERATURE,
            )