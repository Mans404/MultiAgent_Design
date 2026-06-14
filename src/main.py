from fastapi import FastAPI
from routes import base, data, nlp
from helpers.config import get_settings
from stores import LLM_Provider_Factory
from stores.vectordb.VectorDB_Provider_Factory import VectorDB_Provider_Factory
from stores.LLM.templates.template_parser import TemplateParser
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Import Metrics setup
from utils.metrics import setup_metrics

app = FastAPI()

setup_metrics(app)

async def startup_span():
    settings = get_settings()
     
    postgres_connection = f"postgresql+asyncpg://{settings.POSTGRES_USERNAME}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_MAIN_DB}"
    app.db_engine = create_async_engine(postgres_connection, echo=True)
    app.db_client = sessionmaker(app.db_engine, expire_on_commit=False, class_=AsyncSession)
    # app.db_client = app.mongo_conn[settings.MONGODB_DATABASE]

    llm_provider_factory = LLM_Provider_Factory(config=settings)
    vectordb_provider_factory = VectorDB_Provider_Factory(config=settings, db_client=app.db_client)

    # generate client 
    app.generation_client = llm_provider_factory.create_provider(settings.GENERATION_BACKEND)
    app.generation_client.set_generation_model(model_name=settings.GENERATION_MODEL_NAME)

    # embedding client
    app.embedding_client = llm_provider_factory.create_provider(settings.EMBEDDING_BACKEND)
    app.embedding_client.set_embedding_model(model_name=settings.EMBEDDING_MODEL_NAME, embedding_size=settings.EMBEDDING_MODEL_SIZE)
    # vector database client
    app.vectordb_client = vectordb_provider_factory.create_provider(provider_type=settings.VECTOR_DB_BACKEND)
    await app.vectordb_client.connect()
    app.template_parser = TemplateParser(
        default_language = settings.DEFAULT_LANG,
        language = settings.PRIMARY_LANG,
    )


async def shutdown_span():
    app.db_engine.dispose()
    
    app.vectordb_client.disconnect()

# app.router.lifespan.on_startup.append(startup_span)
# app.router.lifespan.on_shutdown.append(shutdown_span)
app.on_event("startup")(startup_span)
app.on_event("shutdown")(shutdown_span)


app.include_router(base.base_router)
app.include_router(data.data_router)
app.include_router(nlp.nlp_router)

