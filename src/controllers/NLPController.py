import json
from .BaseController import BaseController
from models.db_schemes import Project
from models.db_schemes import DataChunk
from stores.LLM.LLM_Enums import Document_Type
from typing import List
from logging import Logger
import logging
import asyncio

# Minimum similarity score to accept a retrieved chunk as relevant.
# Chunks scoring below this threshold are discarded before being passed
# to the generation step. Tune this value for your embedding model:
#   - Too high → many queries return no results (over-filtering)
#   - Too low  → unrelated chunks pollute the context (under-filtering)
# 0.70 is a reasonable starting point for cosine similarity.
RETRIEVAL_SCORE_THRESHOLD = 0.40


class NLPController(BaseController):
    def __init__(self, vectordb_client, generation_client, embedding_client, template_parser):
        super().__init__()
        self.vectordb_client = vectordb_client
        self.generation_client = generation_client
        self.embedding_client = embedding_client
        self.template_parser = template_parser
        self.logger = logging.getLogger(__name__)

    def create_collection_name(self, project_id):
        return f"collection_{project_id}".strip()

    # -------------------------------------------------------------------------
    # VectorDB operations
    # -------------------------------------------------------------------------

    async def reset_vectordb_collection(self, project: Project):
        collection_name = self.create_collection_name(project_id=project.project_id)
        return await self.vectordb_client.delete_collection(collection_name=collection_name)

    async def get_vectordb_collection_info(self, project: Project):
        collection_name = self.create_collection_name(project_id=project.project_id)
        return await self.vectordb_client.get_collection_info(collection_name=collection_name)

    async def index_into_vectodb(self, project: Project, chunks: List[DataChunk],
                                  chunk_model=None,
                                  do_reset: bool = False):
        collection_name = self.create_collection_name(project_id=project.project_id)

        texts = [chunk.chunk_text for chunk in chunks]
        metadata = [chunk.chunk_metadata for chunk in chunks]

        # FIX: pass real DB primary keys (chunk_id) as record_ids instead of
        # letting each provider generate its own IDs (e.g. MD5 hashes).
        # MD5 hashes are derived from chunk text, so two chunks with identical
        # text (duplicate uploads, shared boilerplate paragraphs, etc.) produce
        # the same hash → Qdrant collapses them into one point → duplicate
        # results are returned on search.
        # Using chunk_id (unique integer PK) guarantees each chunk gets a
        # distinct vector record even when the text content is identical.
        record_ids = [chunk.chunk_id for chunk in chunks]

        vectors = [
            self.embedding_client.embed_text(
                text=chunk,
                document_type=Document_Type.DOCUMENT.value
            )
            for chunk in texts
        ]

        await self.vectordb_client.insert_many_data(
            collection_name=collection_name,
            texts=texts,
            metadata=metadata,
            vectors=vectors,
            record_ids=record_ids,   # FIX: was not passed before
        )

        if chunk_model:
            await chunk_model.update_chunks_vectors(
                chunks=chunks,
                vectors=vectors
            )

        return True

    async def search_vector_db_collection(self, project: Project, text: str, top_k: int = 5):
        collection_name = self.create_collection_name(project_id=project.project_id)

        text_vector = self.embedding_client.embed_text(
            text=text, document_type=Document_Type.QUERY.value
        )

        if not text_vector or len(text_vector) == 0:
            self.logger.error("Failed to generate embedding for the query text.")
            return None

        search_results = await self.vectordb_client.search_by_vector(
            collection_name=collection_name,
            vector=text_vector,
            top_k=top_k,
        )

        if not search_results:
            return None
        top_scores = [f"{r['score']:.4f}" for r in search_results]
        self.logger.info(
            f"Raw search returned {len(search_results)} results. "
            f"Top scores: {top_scores}"
        )

        # FIX: filter out low-confidence results.
        # Without a threshold, the top-K results are always returned regardless
        # of how poorly they match the query — leading to unrelated chunks being
        # sent to the LLM and degrading answer quality.
        # We discard any chunk whose similarity score is below RETRIEVAL_SCORE_THRESHOLD.
        # Note: PG_Vector_Provider now also returns scores in the same 0-1 range
        # (cosine similarity, higher = more similar) so this filter works for both
        # Qdrant and PG Vector providers.
        filtered_results = [
            r for r in search_results
            if r["score"] >= RETRIEVAL_SCORE_THRESHOLD
        ]

        if not filtered_results:
            self.logger.warning(
                f"No results above score threshold {RETRIEVAL_SCORE_THRESHOLD} "
                f"for query in collection '{collection_name}'. "
                f"Best score was {max(r['score'] for r in search_results):.4f}."
            )
            return None

        # FIX: Deduplicate results by text content.
        # If the same chunk text appears multiple times in the results
        # (due to duplicate indexing or other issues), keep only the one
        # with the highest score and discard the others.
        seen_texts = {}
        deduplicated_results = []
        duplicates_found = 0
        for result in filtered_results:
            text = result["payload"]["text"]
            if text not in seen_texts:
                seen_texts[text] = len(deduplicated_results)
                deduplicated_results.append(result)
            else:
                # Replace with higher score if this one is better
                existing_idx = seen_texts[text]
                if result["score"] > deduplicated_results[existing_idx]["score"]:
                    deduplicated_results[existing_idx] = result
                duplicates_found += 1

        if duplicates_found > 0:
            self.logger.warning(
                f"Found and removed {duplicates_found} duplicate chunk(s) from search results. "
                f"This may indicate duplicate chunks in the collection."
            )

        return deduplicated_results

    # -------------------------------------------------------------------------
    # RAG pipeline
    # -------------------------------------------------------------------------

    async def answer_query_with_generation(
        self,
        project: Project,
        query: str,
        top_k: int = 5,
        chat_history: list = None,
        max_out_tokens: int = None,
        temperature: float = None,
    ):
        if chat_history is None:
            chat_history = []

        # step 1: retrieve relevant docs (already filtered by score threshold)
        retrieved_docs = await self.search_vector_db_collection(
            project=project,
            text=query,
            top_k=top_k,
        )
        if not retrieved_docs:
            return None, None, chat_history

        # step 2: load and validate required templates
        system_prompt = self.template_parser.get("rag", "system_prompt")
        footer_prompt = self.template_parser.get("rag", "footer_template", {"query": query})

        if not system_prompt or not footer_prompt:
            raise ValueError("Missing required RAG templates: check 'system_prompt' and 'footer_template' keys")

        # step 3: build document prompts
        documents_prompts = []
        for idx, doc in enumerate(retrieved_docs):
            chunk_text = doc["payload"]["text"]
            if hasattr(self.generation_client, "process_text"):
                chunk_text = self.generation_client.process_text(chunk_text)

            prompt = self.template_parser.get("rag", "retrieved_doc_prompt", {
                "doc_num": idx + 1,
                "chunk_text": chunk_text,
            })
            if prompt is None:
                return None, None, chat_history

            documents_prompts.append(prompt)

        if not documents_prompts:
            return None, None, chat_history

        # step 4: build chat history with system prompt
        chat_history = [
            self.generation_client.construct_prompt(
                prompt=system_prompt,
                role=self.generation_client.enums.SYSTEM.value,
            )
        ] + chat_history

        # step 5: assemble full prompt
        full_prompt = "\n".join(documents_prompts) + "\n" + footer_prompt

        # step 6: generate answer
        answer = await self.generation_client.generate_text(
            prompt=full_prompt,
            chat_history=chat_history,
        )
        return answer, full_prompt, chat_history