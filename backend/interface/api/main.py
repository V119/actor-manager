from fastapi import FastAPI
from .routes import router
from ...infrastructure.orm_models import database
from ...infrastructure.config import settings

app = FastAPI(title="Glacier AI Actor API")

@app.on_event("startup")
async def startup():
    if database.is_closed():
        database.init(
            settings.DB_NAME,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            host=settings.DB_HOST,
            port=settings.DB_PORT
        )
        # In a real async setup we would use peewee_async.Manager
        # but for initialization we need to ensure the DB object is configured.

app.include_router(router, prefix="/api")

@app.get("/")
async def root():
    return {"message": "Welcome to Glacier AI Actor API"}
