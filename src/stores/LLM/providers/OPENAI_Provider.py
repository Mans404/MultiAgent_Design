from LLM_Interface import LLM_Interface
from LLM_Enums import LLM_Enums
from openai import OpenAI

class OPENAI_Provider(LLM_Interface):

    def __init__(self, api_key: str,
                    api_url : str = None,
                    default_input_max_chracters: int = 1000,
                    default_output_max_chracters: int = 200,
                    default_temperature: float = 0.7,):
        
        self.api_key = api_key
        self.api_url = api_url
        self.default_input_max_chracters = default_input_max_chracters
        self.default_output_max_chracters = default_output_max_chracters
        self.default_temperature = default_temperature

        self.generation_model_name = None
        self.embedding_model_name = None

        self.embedding_size = None