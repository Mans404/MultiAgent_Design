from ..LLM_Interface import LLM_Interface
from ..LLM_Enums import LLM_Enums, OpenAI_Enums
from openai import OpenAI
import logging
class OPENAI_Provider(LLM_Interface):

    def __init__(self, api_key: str,
                    api_url : str = None,
                    default_input_max_tokens: int = 1000,
                    default_output_max_tokens: int = 200,
                    default_temperature: float = 0.7,model_name: str = None):
        
        self.api_key = api_key
        self.api_url = api_url
        self.default_input_max_tokens = default_input_max_tokens
        self.default_output_max_tokens = default_output_max_tokens
        self.default_temperature = default_temperature

        self.generation_model_name = None
        self.embedding_model_name = None
        self.embedding_size = None


        self.client = OpenAI(api_key=self.api_key, base_url=self.api_url)
        self.enums = OpenAI_Enums
        self.logger = logging.getLogger(__name__)

    def set_generation_model(self, model_name: str):
        self.generation_model_name = model_name

    def set_embedding_model(self, model_name: str, embedding_size: int):
        self.embedding_model_name = model_name
        self.embedding_size = embedding_size
    # I have a question for this code.
    def process_text(self, text: str) -> str:
        return text[0:self.default_input_max_tokens].strip()
    def generate_text(self, prompt: str, max_out_tokens: int = None,
                        chat_history: list=[],
                        temperature: float = None,
                         ) -> str:
        #if it is embedding model.
        if not self.client:
            self.logger.error("OpenAI client was not set")
            return None
        
        if not self.generation_model_name:
            self.logger.error("Generation model for OpenAI was not set")
            return None
        
        max_out_tokens = max_out_tokens if max_out_tokens else self.default_output_max_tokens
        temperature = temperature if temperature else self.default_temperature
    
        chat_history.append(
            self.construct_prompt(prompt = prompt, role = OpenAI_Enums.USER.value)
        )
    
        response = self.client.chat.completions.create(
            model = self.generation_model_name,
            messages = chat_history,
            max_tokens = max_out_tokens,
            temperature = temperature
        )
    
        if not response.choices[0].message.content: # check if the response is empty or not.
            self.logger.error("Error while generating text with OpenAI model")
            return None
        return response.choices[0].message.content

    
    def embed_text(self, text:str, document_type: str = None) -> str:
        if not self.client:
            self.logger.error("OpenAI client was not set")
            return None
        
        if not self.embedding_model_name:
            self.logger.error("Embedding model for OpenAI was not set")
            return None
        
        response = self.client.embeddings.create(
            model = self.embedding_model_name,
            input = text
        )

        if not response or len(response.data) == 0:
            self.logger.error("Error while embedding OpenAI model")
            return None
        
        return response.data[0].embedding
    
    def construct_prompt(self, prompt: str, role: str) -> dict:
        return {
            "role" : role,
            "content" : self.process_text(prompt)
        }