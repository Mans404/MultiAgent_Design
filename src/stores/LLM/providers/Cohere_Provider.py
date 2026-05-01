from LLM_Interface import LLM_Interface
from LLM_Enums import LLM_Enums, Cohere_Enums
import cohere
import logging
class Cohere_Provider(LLM_Interface):
    def __init__(self, api_key: str,
                    
                    default_input_max_tokens: int = 1000,
                    default_output_max_tokens: int = 200,
                    default_temperature: float = 0.7,):
        
        self.api_key = api_key
        self.default_input_max_tokens = default_input_max_tokens
        self.default_output_max_tokens = default_output_max_tokens
        self.default_temperature = default_temperature

        self.generation_model_name = None
        self.embedding_model_name = None
        self.embedding_size = None

        self.client = cohere.Client(api_key=self.api_key)

        self.logger = logging.getLogger(__name__)

    def set_generation_model(self, model_name: str):
        self.generation_model_name = model_name

    def set_embedding_model(self, model_name: str, embedding_size: int):
        self.embedding_model_name = model_name
        self.embedding_size = embedding_size

    def process_text(self, text: str) -> str:
        return text[0:self.default_input_max_tokens].strip()
    

    def generate_text(self, prompt: str, max_out_tokens: int = None,
                        chat_history: list=[],
                        temperature: float = None,
                         ) -> str:
        #if it is embedding model.
        if not self.client:
            self.logger.error("Cohere client was not set")
            return None
        
        if not self.generation_model_name:
            self.logger.error("Generation model for Cohere was not set")
            return None
        
        max_out_tokens = max_out_tokens if max_out_tokens else self.default_output_max_tokens
        temperature = temperature if temperature else self.default_temperature
        
        response = self.client.chat(
            model = self.generation_model_name,
            chat_history=chat_history,
            message=self.process_text(prompt),)
        
        if not response or not response.text:
            self.logger.error("No response from Cohere API")
            return None
        return response.text
    
    def embed_text(self, text, document_type = None):
        if not self.client:
            self.logger.error("Cohere client was not set")
            return None
        
        if not self.embedding_model_name:
            self.logger.error("Embedding model for Cohere was not set")
            return None
        input_type = Cohere_Enums.DOCUMENT.value if document_type == "document" else Cohere_Enums.QUERY.value
        response = self.client.embed(
            model=self.embedding_model_name,
            texts=[self.process_text(text)],
            truncate="END",
            input_type=input_type,
            embedding_types=['float']
        )

        if not response.embeddings.float:
            self.logger.error("No embedding response from Cohere API")
            return None
        return response.embeddings.float[0]
    def construct_prompt(self, prompt, role):
        return {
            "role": role,
            "text": self.process_text(prompt)
        }