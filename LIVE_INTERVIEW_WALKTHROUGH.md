# Live Interview Walkthrough Guide

Use this as a literal speaking script while you open the code in VS Code. The goal is to show a clean story: startup, ingestion, indexing, retrieval, then answer generation.

## 1) 

"This project is a small RAG application. The flow is: the FastAPI app boots, connects to MongoDB and Qdrant, uploads and processes files into chunks, generates embeddings for those chunks, stores them in the vector database, and then uses a retrieval step plus an LLM prompt template to answer questions from the indexed content. I can walk you through the exact code path from request to response."

## 2) Entry Point

Open first: [src/main.py](src/main.py#L11)

Why this file first:

This is where the app is created, startup and shutdown hooks are registered, and all routers are mounted. It is the cleanest way to explain the whole system before diving into details.

What to point at:

- `app = FastAPI()` in [src/main.py](src/main.py#L8)
- `startup_span()` in [src/main.py](src/main.py#L11)
- `shutdown_span()` in [src/main.py](src/main.py#L35)
- `app.include_router(...)` lines in [src/main.py](src/main.py#L45)

What to say:

"I start here because this file wires the runtime. On startup it loads settings, creates the MongoDB client, creates the generation and embedding clients, connects to Qdrant, and loads the prompt templates. Then it mounts the base, data, and NLP routers."

## 3) Step-by-Step Execution Flow

### Step A - API Request Flow

Primary files:

- [src/routes/base.py](src/routes/base.py#L5)
- [src/routes/data.py](src/routes/data.py#L24)
- [src/routes/nlp.py](src/routes/nlp.py#L15)

What to say:

"The API layer is intentionally thin. It receives the request, loads the project record, and delegates the real work to controllers. That keeps the route handlers readable and keeps the business logic in one place."

What to point at:

- `@base_router.get("/")` in [src/routes/base.py](src/routes/base.py#L9)
- `@data_router.post("/upload/{project_id}")` in [src/routes/data.py](src/routes/data.py#L24)
- `@data_router.post("/process/{project_id}")` in [src/routes/data.py](src/routes/data.py#L96)
- `@nlp_router.post("/index/push/{project_id}")` in [src/routes/nlp.py](src/routes/nlp.py#L15)
- `@nlp_router.get("/index/answer/{project_id}")` in [src/routes/nlp.py](src/routes/nlp.py#L138)

### Step B - Upload and Storage

Open:

- [src/routes/data.py](src/routes/data.py#L24)
- [src/controllers/DataController.py](src/controllers/DataController.py#L15)
- [src/controllers/ProjectController.py](src/controllers/ProjectController.py#L11)
- [src/models/AssetModel.py](src/models/AssetModel.py#L37)

What to say:

"The upload endpoint validates the file, writes it to the project folder, and stores a file asset record in MongoDB. So the application keeps the raw file on disk and keeps metadata in the database."

What to point at:

- `validate_uploaded_file()` in [src/controllers/DataController.py](src/controllers/DataController.py#L15)
- `generate_unique_filepath()` in [src/controllers/DataController.py](src/controllers/DataController.py#L25)
- `get_project_path()` in [src/controllers/ProjectController.py](src/controllers/ProjectController.py#L11)
- `create_asset()` in [src/models/AssetModel.py](src/models/AssetModel.py#L29)

### Step C - Query Processing Pipeline

Open:

- [src/routes/data.py](src/routes/data.py#L96)
- [src/controllers/ProcessController.py](src/controllers/ProcessController.py#L17)
- [src/models/ChunkModel.py](src/models/ChunkModel.py#L36)
- [src/models/db_schemes/data_chunk.py](src/models/db_schemes/data_chunk.py#L1)

What to say:

"Processing reads the stored file, splits it into chunks, and converts each chunk into a database record. This is the bridge between the raw document and the retrieval layer."

What to point at:

- `get_file_loader()` in [src/controllers/ProcessController.py](src/controllers/ProcessController.py#L20)
- `get_file_content()` in [src/controllers/ProcessController.py](src/controllers/ProcessController.py#L39)
- `process_file_content()` in [src/controllers/ProcessController.py](src/controllers/ProcessController.py#L47)
- `insert_many_chunks()` in [src/models/ChunkModel.py](src/models/ChunkModel.py#L49)
- `DataChunk.get_indexes()` in [src/models/db_schemes/data_chunk.py](src/models/db_schemes/data_chunk.py#L10)

### Step D - Embedding Generation

Open:

- [src/controllers/NLPController.py](src/controllers/NLPController.py#L28)
- [src/stores/LLM/LLM_Provider_Factory.py](src/stores/LLM/LLM_Provider_Factory.py#L1)
- [src/stores/LLM/providers/OPENAI_Provider.py](src/stores/LLM/providers/OPENAI_Provider.py#L37)
- [src/stores/LLM/providers/Cohere_Provider.py](src/stores/LLM/providers/Cohere_Provider.py#L37)

What to say:

"Embedding generation happens in the NLP controller. For each chunk, the code calls the embedding client and converts the text into a vector. The factory decides which provider implementation to use, so the rest of the app does not care whether that is OpenAI or Cohere."

What to point at:

- `index_into_vectodb()` in [src/controllers/NLPController.py](src/controllers/NLPController.py#L28)
- `create_provider()` in [src/stores/LLM/LLM_Provider_Factory.py](src/stores/LLM/LLM_Provider_Factory.py#L10)
- `set_embedding_model()` and `embed_text()` in [src/stores/LLM/providers/OPENAI_Provider.py](src/stores/LLM/providers/OPENAI_Provider.py#L32)
- `embed_text()` in [src/stores/LLM/providers/Cohere_Provider.py](src/stores/LLM/providers/Cohere_Provider.py#L54)

### Step E - Vector Database Retrieval

Open:

- [src/controllers/NLPController.py](src/controllers/NLPController.py#L56)
- [src/stores/vectordb/providers/QdrantDB.py](src/stores/vectordb/providers/QdrantDB.py#L46)
- [src/stores/vectordb/providers/QdrantDB.py](src/stores/vectordb/providers/QdrantDB.py#L121)

What to say:

"The query text is embedded the same way as the chunks. Then the vector database runs a similarity search and returns the most relevant stored chunks. That is the retrieval in RAG."

What to point at:

- `search_vector_db_collection()` in [src/controllers/NLPController.py](src/controllers/NLPController.py#L56)
- `create_collection()` in [src/stores/vectordb/providers/QdrantDB.py](src/stores/vectordb/providers/QdrantDB.py#L46)
- `insert_many_data()` in [src/stores/vectordb/providers/QdrantDB.py](src/stores/vectordb/providers/QdrantDB.py#L85)
- `search_by_vector()` in [src/stores/vectordb/providers/QdrantDB.py](src/stores/vectordb/providers/QdrantDB.py#L121)

### Step F - Context Building

Open:

- [src/controllers/NLPController.py](src/controllers/NLPController.py#L68)
- [src/stores/LLM/templates/template_parser.py](src/stores/LLM/templates/template_parser.py#L13)
- [src/stores/LLM/templates/locales/en/rag.py](src/stores/LLM/templates/locales/en/rag.py#L1)

What to say:

"This is where retrieval becomes a prompt. The controller loads the system prompt, loads one template per retrieved chunk, and then combines them into a final prompt with a footer and the user question. That is the context assembly step."

What to point at:

- `answer_query_with_generation()` in [src/controllers/NLPController.py](src/controllers/NLPController.py#L68)
- `TemplateParser.get()` in [src/stores/LLM/templates/template_parser.py](src/stores/LLM/templates/template_parser.py#L13)
- `system_prompt`, `retrieved_doc_prompt`, and `footer_template` in [src/stores/LLM/templates/locales/en/rag.py](src/stores/LLM/templates/locales/en/rag.py#L1)

### Step G - LLM Generation

Open:

- [src/controllers/NLPController.py](src/controllers/NLPController.py#L68)
- [src/stores/LLM/providers/OPENAI_Provider.py](src/stores/LLM/providers/OPENAI_Provider.py#L37)
- [src/stores/LLM/LLM_Interface.py](src/stores/LLM/LLM_Interface.py#L1)

What to say:

"Once the prompt is built, the generation client receives the final prompt and the chat history. The model then produces the answer constrained by the retrieved documents and the system instructions."

What to point at:

- `chat_history` assembly inside `answer_query_with_generation()` in [src/controllers/NLPController.py](src/controllers/NLPController.py#L68)
- `generate_text()` in [src/stores/LLM/providers/OPENAI_Provider.py](src/stores/LLM/providers/OPENAI_Provider.py#L37)
- `construct_prompt()` in [src/stores/LLM/providers/OPENAI_Provider.py](src/stores/LLM/providers/OPENAI_Provider.py#L92)

## 4) Live Debugging Style Walkthrough

Use this as a script while stepping through the app:

1. Start at [src/main.py](src/main.py#L11) and say, "This is the boot sequence. I am watching startup wire the clients and routers."
2. Move to [src/routes/data.py](src/routes/data.py#L24) and say, "The upload endpoint only validates and persists the file, it does not do retrieval yet."
3. Step into [src/controllers/DataController.py](src/controllers/DataController.py#L15) and say, "Here the code checks type and size before writing to disk."
4. Jump to [src/routes/data.py](src/routes/data.py#L96) and say, "Now the file is being converted into chunks."
5. Open [src/controllers/ProcessController.py](src/controllers/ProcessController.py#L47) and say, "This split is what prepares text for embeddings and vector search."
6. Switch to [src/routes/nlp.py](src/routes/nlp.py#L15) and say, "This pushes the processed chunks into the vector database."
7. Open [src/controllers/NLPController.py](src/controllers/NLPController.py#L28) and say, "Here each chunk becomes a vector and gets indexed."
8. Move to [src/routes/nlp.py](src/routes/nlp.py#L138) and say, "This is the answer path. The query is embedded, retrieved, and then turned into a final prompt."
9. End at [src/controllers/NLPController.py](src/controllers/NLPController.py#L68) and say, "This is the last hop: prompt assembly plus generation."

## 5) Common Interview Interruptions and Short Answers

### While on startup

Question: "Why do you create both embedding and generation clients at startup?"

Answer: "To avoid repeated initialization on every request and to keep the request path focused on the actual work."

Question: "Why connect to Qdrant in startup?"

Answer: "So the vector database connection is ready before the first request and failures surface early."

### While on upload and processing

Question: "Why store files on disk and metadata in MongoDB?"

Answer: "Disk keeps the raw document, MongoDB keeps structured references and chunk metadata."

Question: "Why do you chunk the file before embedding?"

Answer: "Chunking keeps retrieval granular and reduces the chance of sending huge, noisy context to the model."

Question: "What happens if a file is invalid?"

Answer: "The controller returns a clear error signal before any file is written or processed."

### While on embeddings and vector search

Question: "Why embed the chunks and the query with the same model?"

Answer: "Because similarity search only works properly when both are in the same vector space."

Question: "Why use Qdrant here?"

Answer: "It gives fast nearest-neighbor retrieval over stored embeddings, which is the core retrieval layer."

Question: "What if no vectors are found?"

Answer: "The controller returns `None` and the route responds with a failure signal instead of inventing an answer."

### While on prompt building and generation

Question: "Where is the context assembled?"

Answer: "In `answer_query_with_generation()`, where the retrieved documents are converted into prompt fragments and joined with the footer and user query."

Question: "How do you keep the answer grounded?"

Answer: "The system prompt tells the model to use only the retrieved documents, and the prompt includes those documents explicitly."

Question: "Why use a template parser?"

Answer: "It separates prompt text from logic, which makes the prompt easier to edit and localize."

## 6) Closing Summary

What to say:

"So the complete flow is: FastAPI receives the request, files are uploaded and processed into chunks, embeddings are generated for each chunk, Qdrant stores and retrieves the vectors, the retrieved chunks are assembled into a prompt, and the LLM generates the final answer. The code is split cleanly so each stage is easy to inspect and debug."

If they ask for the one-sentence takeaway:

"This is a classic RAG pipeline with a clear separation between ingestion, retrieval, and generation."

## 7) Best Live Demo Order

If you only have a few minutes, open files in this order:

1. [src/main.py](src/main.py#L11)
2. [src/routes/data.py](src/routes/data.py#L24)
3. [src/controllers/ProcessController.py](src/controllers/ProcessController.py#L47)
4. [src/routes/nlp.py](src/routes/nlp.py#L15)
5. [src/controllers/NLPController.py](src/controllers/NLPController.py#L28)
6. [src/stores/vectordb/providers/QdrantDB.py](src/stores/vectordb/providers/QdrantDB.py#L121)
7. [src/stores/LLM/templates/locales/en/rag.py](src/stores/LLM/templates/locales/en/rag.py#L1)

That sequence shows the whole system in the fewest jumps.