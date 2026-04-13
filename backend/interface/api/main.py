from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from backend.config import get_config
from backend.interface.api.auth_routes import router as auth_router
from backend.interface.api.middleware import LogRequestMiddleware, TraceIdMiddleware
from backend.interface.api.routes import router
from backend.infrastructure.orm_models import database
from backend.infrastructure.config import settings
from backend.logging_config import setup_logging_config

# Ensure logging is initialized in the actual app process as well.
# This is required when uvicorn runs with reload (child process) or when
# the app is started directly via `uvicorn backend.interface.api.main:app`.
setup_logging_config()

app = FastAPI(title=str(get_config("api.title", "Glacier AI Actor API")))
logger = logging.getLogger(__name__)

app.add_middleware(LogRequestMiddleware)
app.add_middleware(TraceIdMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(get_config("api.cors.allow_origins", [])),
    allow_credentials=bool(get_config("api.cors.allow_credentials", True)),
    allow_methods=list(get_config("api.cors.allow_methods", ["*"])),
    allow_headers=list(get_config("api.cors.allow_headers", ["*"])),
)

@app.on_event("startup")
async def startup():
    logger.info(
        "API startup begin host=%s port=%s db=%s minio=%s",
        settings.DB_HOST,
        settings.DB_PORT,
        settings.DB_NAME,
        settings.MINIO_ENDPOINT,
    )
    database.init(
        settings.DB_NAME,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        host=settings.DB_HOST,
        port=settings.DB_PORT
    )
    if database.is_closed():
        await database.aio_connect()
    logger.info("API startup completed: database connected")

@app.on_event("shutdown")
async def shutdown():
    if not database.is_closed():
        await database.aio_close()
    logger.info("API shutdown completed: database disconnected")

app.include_router(router, prefix="/api")
app.include_router(auth_router, prefix="/api")

@app.get("/")
async def root():
    return {"message": str(get_config("api.root_message", "Welcome to Glacier AI Actor API"))}
