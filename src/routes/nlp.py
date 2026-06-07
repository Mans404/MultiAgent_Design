import json

from fastapi import FastAPI, APIRouter, status, Request
from fastapi.responses import JSONResponse

from stores.LLM.templates import template_parser
from .schemes.nlp import PushRequest, SearchRequest
from models.ProjectModel import ProjectModel
from models.ChunkModel import ChunkModel
from controllers.NLPController import NLPController
from models.enums.ResponseEnums import ResponseSignal
from tqdm.auto import tqdm

nlp_router = APIRouter(
    prefix="/api/v1/nlp",
    tags=["api_v1", "nlp"],
)


@nlp_router.post("/index/push/{project_id}")
async def index_data(request: Request, project_id: int, push_request: PushRequest):

    project_model = await ProjectModel.create_instance(
        db_client=request.app.db_client,
    )

    chunk_model = await ChunkModel.create_instance(
        db_client=request.app.db_client
    )

    project = await project_model.get_project_or_create_one(
        project_id=project_id
    )

    if not project:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "signal": ResponseSignal.PROJECT_NOT_FOUND.value
            }
        )

    nlp_controller = NLPController(
        vectordb_client=request.app.vectordb_client,
        generation_client=request.app.generation_client,
        embedding_client=request.app.embedding_client,
        template_parser=request.app.template_parser,
    )

    has_records = True
    page_no = 1
    inserted_items_count = 0

    # create collection if not exists
    collection_name = nlp_controller.create_collection_name(project_id=project.project_id)

    _ = await request.app.vectordb_client.create_collection(
        collection_name=collection_name,
        dimension=request.app.embedding_client.embedding_size,
        do_reset=push_request.do_reset,
    )

    # Setup Batching
    total_chunks_count = await chunk_model.get_total_chunks_count(project_id=project.project_id)
    pbar = tqdm(total=total_chunks_count, desc="Indexing Chunks into VectorDB", position=0)

    while has_records:

        chunks = await chunk_model.get_project_chunks(
            project_id=project.project_id,
            page_no=page_no
        )

        print(f"Page {page_no} chunks count = {len(chunks)}")

        if not chunks:
            has_records = False
            break

        page_no += 1

        is_inserted = await nlp_controller.index_into_vectodb(
            project=project,
            chunks=chunks,
            chunk_model=chunk_model,
        )

        if not is_inserted:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "signal": ResponseSignal.PROCESSING_FAILED.value
                }
            )

        pbar.update(len(chunks))
        inserted_items_count += len(chunks)

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "signal": ResponseSignal.INSERT_INTO_VECTORDB_SUCCESS.value,
            "inserted_count": inserted_items_count,
        }
    )


@nlp_router.get("/index/info/{project_id}")
async def get_project_index_info(request: Request, project_id: int):
    project_model = await ProjectModel.create_instance(
        db_client=request.app.db_client,
    )
    project = await project_model.get_project_or_create_one(project_id=project_id)

    nlp_controller = NLPController(
        vectordb_client=request.app.vectordb_client,
        generation_client=request.app.generation_client,
        embedding_client=request.app.embedding_client,
        template_parser=request.app.template_parser,
    )
    collection_info = await nlp_controller.get_vectordb_collection_info(project=project)
    collection_info_json = json.loads(json.dumps(collection_info, default=lambda x: x.__dict__))
    return JSONResponse(
        content={
            "signal": ResponseSignal.VECTOR_COLLECTION_RETRIEVE_SUCCESS.value,
            "collection_info": collection_info_json
        }
    )


@nlp_router.get("/index/search/{project_id}")
async def search_index(request: Request, project_id: int, search_request: SearchRequest):
    project_model = await ProjectModel.create_instance(
        db_client=request.app.db_client,
    )
    project = await project_model.get_project_or_create_one(project_id=project_id)

    nlp_controller = NLPController(
        vectordb_client=request.app.vectordb_client,
        generation_client=request.app.generation_client,
        embedding_client=request.app.embedding_client,
        template_parser=request.app.template_parser,
    )

    results = await nlp_controller.search_vector_db_collection(
        project=project,
        text=search_request.text,
        top_k=search_request.top_k,
    )

    # FIX: results can be None when:
    #   (a) the collection is empty
    #   (b) the query embedding failed
    #   (c) all retrieved chunks scored below RETRIEVAL_SCORE_THRESHOLD
    # Iterating over None crashes with TypeError. Return a clear 404 instead.
    if results is None:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "signal": ResponseSignal.NO_RESULTS_FOUND.value,
                "results": [],
            }
        )

    return JSONResponse(
        content={
            "signal": ResponseSignal.VECTOR_COLLECTION_RETRIEVE_SUCCESS.value,
            "results": [
                {
                    "score": r["score"],
                    "text": r["payload"].get("text") if r["payload"] else None,
                }
                for r in results
            ]
        }
    )


@nlp_router.post("/index/answer/{project_id}")
async def answer_query(request: Request, project_id: int, search_request: SearchRequest):
    project_model = await ProjectModel.create_instance(
        db_client=request.app.db_client,
    )
    project = await project_model.get_project_or_create_one(project_id=project_id)

    nlp_controller = NLPController(
        vectordb_client=request.app.vectordb_client,
        generation_client=request.app.generation_client,
        embedding_client=request.app.embedding_client,
        template_parser=request.app.template_parser,
    )

    answer, full_prompt, chat_history = await nlp_controller.answer_query_with_generation(
        project=project,
        query=search_request.text,
        top_k=search_request.top_k,
    )

    # FIX: `not answer` is True for empty string "" as well as None,
    # which would incorrectly reject a valid (but empty-looking) answer.
    # Use an explicit `is None` check so only a genuine failure triggers the error response.
    if answer is None:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "signal": ResponseSignal.ANSWER_GENERATION_FAILED.value,
            }
        )

    return JSONResponse(
        content={
            "signal": ResponseSignal.ANSWER_GENERATION_SUCCESS.value,
            "answer": answer,
            "full_prompt": full_prompt,
            "chat_history": [str(msg) for msg in chat_history],
        }
    )