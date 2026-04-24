from abc import ABC, abstractmethod


class LLM_Interface(ABC):

    @abstractmethod
    def set_generation_model(self, model_name: str):
        pass

    @abstractmethod
    def set_embedding_model(self, model_name: str):
        pass

    @abstractmethod
    def generate_text(self, prompt: str, max_tokens: int = 100, temperature: float = None) -> str:
        pass

    @abstractmethod
    def embed_text(self, text:str, document_type: str) -> str:
        pass

    @abstractmethod
    def construct_prompt(self, prompt: str, role: str) -> str:
        pass


    
    