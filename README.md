# Mini RAG App

Mini RAG App is a FastAPI project that builds a simple Retrieval-Augmented Generation pipeline.
It uploads documents, splits them into chunks, creates embeddings, stores vectors in Qdrant, and uses the retrieved context to answer user questions with an LLM.

## What this project does

- Uploads text and PDF files for each project
- Stores file metadata in MongoDB
- Splits documents into smaller chunks
- Generates embeddings for each chunk
- Saves vectors in Qdrant
- Retrieves the most relevant chunks for a query
- Builds a prompt from retrieved context and generates the final answer

## Flowchart

```mermaid
flowchart TD
		A[User uploads a file] --> B[POST /api/v1/data/upload/{project_id}]
		B --> C[Save file on disk]
		C --> D[Save file metadata in MongoDB]
		D --> E[POST /api/v1/data/process/{project_id}]
		E --> F[Load TXT or PDF content]
		F --> G[Split document into chunks]
		G --> H[Save chunks in MongoDB]
		H --> I[POST /api/v1/nlp/index/push/{project_id}]
		I --> J[Create embeddings for each chunk]
		J --> K[Store vectors in Qdrant]
		L[User asks a question] --> M[POST /api/v1/nlp/index/answer/{project_id}]
		M --> N[Embed the query]
		N --> O[Search top-k similar chunks in Qdrant]
		O --> P[Build prompt with retrieved context]
		P --> Q[LLM generates the answer]
```

## How the project works

### 1. App startup

The app starts from [src/main.py](src/main.py). On startup it loads settings, creates the MongoDB client, creates the generation and embedding clients, connects to Qdrant, and loads the prompt templates.

### 2. Upload stage

The upload endpoint is [POST /api/v1/data/upload/{project_id}](src/routes/data.py).
It validates the uploaded file, saves it on disk, and stores file metadata in MongoDB.

### 3. Processing stage

The processing endpoint is [POST /api/v1/data/process/{project_id}](src/routes/data.py).
It loads the saved file, reads TXT or PDF content, and splits the text into chunks using recursive character chunking.

### 4. Indexing stage

The indexing endpoint is [POST /api/v1/nlp/index/push/{project_id}](src/routes/nlp.py).
It reads the stored chunks, creates embeddings, and saves the vectors in Qdrant.

### 5. Question answering stage

The answer endpoint is [POST /api/v1/nlp/index/answer/{project_id}](src/routes/nlp.py).
It embeds the question, finds the most relevant chunks, builds a prompt from the retrieved context, and sends it to the LLM.

## Tech stack

- FastAPI
- MongoDB with Motor
- Qdrant vector database
- OpenAI and Cohere SDKs
- LangChain loaders and text splitters
- PyMuPDF for PDF reading
- Uvicorn

## Main libraries

See [src/requirements.txt](src/requirements.txt) for the full list.
The main runtime dependencies are FastAPI, Motor, Qdrant Client, LangChain, PyMuPDF, OpenAI, and Cohere.

## Configuration

The app reads its settings from [src/helpers/config.py](src/helpers/config.py) and an `.env` file.

Typical settings include:

- `MONGODB_URL`
- `MONGODB_DATABASE`
- `GENERATION_BACKEND`
- `EMBEDDING_BACKEND`
- `OPENAI_API_KEY`
- `OPENAI_API_URL`
- `COHERE_API_KEY`
- `GENERATION_MODEL_NAME`
- `EMBEDDING_MODEL_NAME`
- `EMBEDDING_MODEL_SIZE`
- `VECTOR_DB_BACKEND`
- `VECTOR_DB_PATH`

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r src/requirements.txt
```

## Run locally

```bash
uvicorn src.main:app --reload
```

## API endpoints

- `POST /api/v1/data/upload/{project_id}` - upload a document
- `POST /api/v1/data/process/{project_id}` - split the document into chunks
- `POST /api/v1/nlp/index/push/{project_id}` - index chunks into Qdrant
- `GET /api/v1/nlp/index/info/{project_id}` - show vector collection info
- `GET /api/v1/nlp/index/search/{project_id}` - search similar chunks
- `POST /api/v1/nlp/index/answer/{project_id}` - generate an answer from retrieved context

## Project structure

```text
src/
	main.py
	controllers/
	helpers/
	models/
	routes/
	stores/
```

## Short walkthrough

If you want to explain the project in a few words, use this flow:

1. Upload a file
2. Process it into chunks
3. Create embeddings
4. Store vectors in Qdrant
5. Retrieve relevant chunks
6. Generate the final answer

## Notes

- The project supports both text and PDF documents.
- Chunk size and overlap can be adjusted during processing.
- The answer generation step uses retrieved context, so it behaves like a classic RAG app.