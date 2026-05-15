from fastapi import FastAPI, APIRouter, status, Request
from fastapi.responses import JSONResponse
from .schemes.nlp import PushRequest
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
        db_client= request.app.db_client
    )
    project = await project_model.get_project_or_create_one(project_id = project_id)

    if not project:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content = {
                "signal" : ResponseSignal.PROJECT_NOT_FOUND.value
            }
        )
    nlp_controller = NLPController(
        vectordb_client=request.app.vectordb_client,
        generation_client=request.app.generation_client,
        embedding_client=request.app.embedding_client,
    )

    has_records = True
    page_no = 1

    # Check this part, it may cause performance issue when there are too many chunks for a project, we can optimize it by using batch processing
    while has_records:
        chunks = await chunk_model.get_project_chunks(project_id=project.id, page_no=page_no)
        if not chunks:
            has_records = False
            break
        # process `chunks` here (existing processing logic should be placed below)
        page_no += 1

        is_inserted = nlp_controller.index_into_vectodb(
            project = project,
            chunks = chunks,
            do_reset = push_request.do_reset
        )
        if not is_inserted:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content = {
                    "signal" : ResponseSignal.PROCESSING_FAILED.value
                }
            )
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content = {
                "signal" : ResponseSignal.INSERT_INTO_VECTORDB_SUCCESS.value
            }
        )