from enum import Enum

class LLM_Enums(Enum):
    OPENAI = "openai"
    COHERE = "cohere"

class OpenAI_Enums(Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"