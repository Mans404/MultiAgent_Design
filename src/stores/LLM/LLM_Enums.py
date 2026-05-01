from enum import Enum

class LLM_Enums(Enum):
    OPENAI = "openai"
    COHERE = "cohere"

class OpenAI_Enums(Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
class Cohere_Enums(Enum):
    SYSTEM = "SYSTEM"
    USER = "USER"
    ASSISTANT = "CHATBOT"
    DOCUMENT = "search_document"
    QUERY = "search_query"

class Document_Type(Enum):
    DOCUMENT = "document"
    QUERY = "query"