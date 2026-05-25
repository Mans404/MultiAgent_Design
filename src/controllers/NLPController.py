import json
from .BaseController import BaseController
from models.db_schemes.project import Project
from models.db_schemes.data_chunk import DataChunk
from stores.LLM.LLM_Enums import Document_Type
from typing import List
from logging import Logger

class NLPController(BaseController):
    def __init__(self, vectordb_client, generation_client, embedding_client, template_parser):
        super().__init__()
        self.vectordb_client = vectordb_client
        self.generation_client = generation_client
        self.embedding_client = embedding_client
        self.template_parser = template_parser

    def create_collection_name(self, project_id):
        return f"collection_{project_id}".strip()

    def reset_vectordb_collection(self, project: Project):
        collection_name = self.create_collection_name(project_id=project.project_id)
        return self.vectordb_client.delete_collection(collection_name=collection_name)

    def get_vectordb_collection_info(self, project: Project):
        collection_name = self.create_collection_name(project_id=project.project_id)
        return self.vectordb_client.get_collection_info(collection_name=collection_name)

    def index_into_vectodb(self, project: Project, chunks: List[DataChunk], do_reset: bool = False):
        # step1: get collection name
        collection_name = self.create_collection_name(project_id=project.project_id)

        # step2: prepare items
        texts = [chunk.chunk_text for chunk in chunks]
        metadata = [chunk.chunk_metadata for chunk in chunks]
        vectors = [
            self.embedding_client.embed_text(text=text, document_type=Document_Type.QUERY.value)
            for text in texts
        ]

        # step3: create collection if not exists
        self.vectordb_client.create_collection(
            collection_name=collection_name,
            dimension=self.embedding_client.embedding_size,
            do_reset=do_reset
        )

        # step4: insert into vectordb
        self.vectordb_client.insert_many_data(
            collection_name=collection_name,
            texts=texts,
            metadata=metadata,
            vectors=vectors
        )
        return True

    def search_vector_db_collection(self, project: Project, text: str, top_k: int = 5):
        collection_name = self.create_collection_name(project_id=project.project_id)
        text_vector = self.embedding_client.embed_text(text=text, document_type=Document_Type.QUERY.value)
        search_results = self.vectordb_client.search_by_vector(
            collection_name=collection_name,
            vector=text_vector,
            top_k=top_k
        )
        if not search_results:
            return None
        return json.loads(json.dumps(search_results, default=lambda x: x.__dict__))

    def answer_query_with_generation(
        self,
        project: Project,
        query: str,
        top_k: int = 5,
        chat_history: list = None,
        max_out_tokens: int = None,
        temperature: float = None
    ):
        # fix mutable default argument
        if chat_history is None:
            chat_history = []

        # step1: retrieve relevant docs
        retrieved_docs = self.search_vector_db_collection(
            project=project,
            text=query,
            top_k=top_k
        )
        if not retrieved_docs:
            return None, None, chat_history 

        # step2: load and validate required templates
        system_prompt = self.template_parser.get("rag", "system_prompt")
        footer_prompt = self.template_parser.get("rag", "footer_template")

        if not system_prompt or not footer_prompt:
            raise ValueError("Missing required RAG templates: check 'system_prompt' and 'footer_template' keys")

        # step3: build document prompts
        documents_prompts = []
        for idx, doc in enumerate(retrieved_docs):
            prompt = self.template_parser.get("rag", "retrieved_doc_prompt", {
                "doc_num": idx + 1,
                "chunk_text": doc["payload"]["text"],
            })
            if prompt is None:
                return None, None, chat_history
                
            documents_prompts.append(prompt)

        if not documents_prompts:
            return None, None, chat_history

        # step4: build chat history with system prompt
        chat_history = [
            self.generation_client.construct_prompt(
                prompt=system_prompt,
                role=self.generation_client.enums.SYSTEM.value
            )
        ] + chat_history

        # step5: assemble full prompt
        full_prompt = "\n".join(documents_prompts) + "\n" + footer_prompt + "\n" + query

        # step6: generate answer
        answer = self.generation_client.generate_text(
            prompt=full_prompt,
            chat_history=chat_history,
        )
        return answer, full_prompt, chat_history