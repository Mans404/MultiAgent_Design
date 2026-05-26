import json

from fastapi import FastAPI, APIRouter, status, Request
from fastapi.responses import JSONResponse

from stores.LLM.templates import template_parser
from .schemes.nlp import PushRequest, SearchRequest
from models.ProjectModel import ProjectModel
from models.ChunkModel import ChunkModel
from controllers.NLPController import NLPController 
from models.enums.ResponseEnums import ResponseSignal
nlp_router = APIRouter(
    prefix="/api/v1/nlp",
    tags=["api_v1", "nlp"],
)

@nlp_router.post("/index/push/{project_id}")
async def index_data(request: Request, project_id: str, push_request: PushRequest):

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

    while has_records:

        chunks = await chunk_model.get_project_chunks(
            project_id=project.id,
            page_no=page_no
        )

        print(f"Page {page_no} chunks count = {len(chunks)}")

        if not chunks:
            has_records = False
            break

        page_no += 1

        is_inserted = nlp_controller.index_into_vectodb(
            project=project,
            chunks=chunks,
            do_reset=push_request.do_reset
        )

        if not is_inserted:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "signal": ResponseSignal.PROCESSING_FAILED.value
                }
            )

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "signal": ResponseSignal.INSERT_INTO_VECTORDB_SUCCESS.value
        }
    )
@nlp_router.get("/index/info/{project_id}")
async def get_project_index_info(request: Request, project_id: str):
    project_model = await ProjectModel.create_instance(
        db_client=request.app.db_client,
        
    )
    project = await project_model.get_project_or_create_one(project_id = project_id)

    nlp_controller = NLPController(
        vectordb_client=request.app.vectordb_client,
        generation_client=request.app.generation_client,
        embedding_client=request.app.embedding_client,
        template_parser=request.app.template_parser,
    )
    collection_info = nlp_controller.get_vectordb_collection_info(project=project)
    collection_info_json = json.loads(json.dumps(collection_info, default=lambda x: x.__dict__))
    return JSONResponse(
        content={
            "signal":ResponseSignal.VECTOR_COLLECTION_RETRIEVE_SUCCESS.value,
            "collection_info":collection_info_json
        })
@nlp_router.get("/index/search/{project_id}")
async def search_index(request: Request, project_id: str, search_request: SearchRequest):
    project_model = await ProjectModel.create_instance(
        db_client=request.app.db_client,
        
    )
    project = await project_model.get_project_or_create_one(project_id = project_id)

    nlp_controller = NLPController(
        vectordb_client=request.app.vectordb_client,
        generation_client=request.app.generation_client,
        embedding_client=request.app.embedding_client,
        template_parser = request.app.template_parser,
    )

    results = nlp_controller.search_vector_db_collection(
    project=project,
    text=search_request.text,
    top_k=search_request.top_k
)

    return JSONResponse(
        content={
            "signal": ResponseSignal.VECTOR_COLLECTION_RETRIEVE_SUCCESS.value,
            "results": [
                {
                    # "id": str(r["id"]),
                    "score": r["score"],
                    "text": r["payload"].get("text") if r["payload"] else None,
                    # "metadata": r["payload"].get("metadata") if r["payload"] else None,
                }
                for r in results
            ]
        }
    )

@nlp_router.get("/index/answer/{project_id}")
async def answer_query(request: Request, project_id: str, search_request: SearchRequest):
    project_model = await ProjectModel.create_instance(
        db_client=request.app.db_client,
        
    )
    project = await project_model.get_project_or_create_one(project_id = project_id)

    nlp_controller = NLPController(
        vectordb_client=request.app.vectordb_client,
        generation_client=request.app.generation_client,
        embedding_client=request.app.embedding_client,
        template_parser = request.app.template_parser,
    )

    answer, full_prompt, chat_history = nlp_controller.answer_query_with_generation(
        project=project,
        query=search_request.text,
        top_k=search_request.top_k
    )

    if not answer:
        return JSONResponse(
            content={
                "signal": ResponseSignal.ANSWER_GENERATION_FAILED.value,
                
            }
        )
    return JSONResponse(
        content={
            "signal": ResponseSignal.ANSWER_GENERATION_SUCCESS.value,
            "answer": answer,
            "full_prompt": full_prompt,
            "chat_history": [str(msg) for msg in chat_history]  # or .dict() if Pydantic models
        }
    )