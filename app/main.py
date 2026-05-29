from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.models import ErrorResponse
from app.routers import chat, documents, health, retrieval

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title="RAG 检索系统",
    description="基于向量数据库和大语言模型的检索增强生成系统",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1")
app.include_router(retrieval.router, prefix="/api/v1")
app.include_router(documents.router, prefix="/api/v1")

app.mount("/", StaticFiles(directory="./web/dist", html=True))


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=ErrorResponse(
            code="INVALID_REQUEST",
            message=str(exc.errors()[0]["msg"]),
            details=exc.errors(),
            request_id=str(id(request)),
        ).model_dump(),
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            code="INTERNAL_ERROR",
            message=str(exc),
            request_id=str(id(request)),
        ).model_dump(),
    )


@app.get("/")
async def root():
    return {"name": "RAG 检索系统 API", "version": "1.0.0"}
