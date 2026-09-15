"""FastAPI application entry point."""
import structlog
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import create_tables
from app.api.health import router as health_router
from app.api.sessions import router as sessions_router
from app.api.chat import router as chat_router
from app.api.artifacts import router as artifacts_router

structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.JSONRenderer(),
    ]
)
log = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("startup", env=settings.environment, provider=settings.llm_provider)
    try:
        await create_tables()
        log.info("database_ready")
    except Exception as e:
        log.warning("database_unavailable", error=str(e))
        log.warning("app_starting_without_db")
    yield
    log.info("shutdown")


app = FastAPI(
    title="Lenny Growth Assistant",
    description="AI-powered growth advisor trained on Lenny's Podcast",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    log.error("unhandled_error", path=request.url.path, error=str(exc))
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)},
    )


app.include_router(health_router)
app.include_router(sessions_router)
app.include_router(chat_router)
app.include_router(artifacts_router)


@app.get("/")
async def root():
    return {"name": "Lenny Growth Assistant API", "version": "1.0.0", "docs": "/docs"}
