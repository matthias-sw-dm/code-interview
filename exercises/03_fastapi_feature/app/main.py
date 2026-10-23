import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.middleware.logging import RequestLoggingMiddleware
from app.routes import health, users

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # TODO: setup and dispose of db
    yield


app = FastAPI(title="User Service", version="1.0.0", lifespan=lifespan)

app.add_middleware(RequestLoggingMiddleware)

app.include_router(health.router)
app.include_router(users.router, prefix="/users")
