from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from app.config import settings
from app.api.health import router as health_router
import structlog
import logging

# ─── Logging ──────────────────────────────────────────────────────────────────
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.add_log_level,
        structlog.processors.JSONRenderer(),
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
)
logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO))
logger = structlog.get_logger()


# ─── Lifespan ─────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("startup.begin", environment=settings.environment, llm_provider=settings.llm_provider)
    
    # Create DB tables
    if settings.database_url:
        try:
            from app.database import create_tables
            await create_tables()
        except Exception as e:
            logger.error("startup.db_failed", error=str(e))
    else:
        logger.warning("startup.no_database_url", hint="Set DATABASE_URL in .env")

    logger.info("startup.complete")
    yield
    logger.info("shutdown.complete")


# ─── App ──────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Lenny Growth Assistant API",
    description="AI-powered assistant grounded in Lenny's Podcast transcripts",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Global error handler ─────────────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("unhandled_error", path=request.url.path, error=str(exc))
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc) if settings.environment == "development" else None},
    )


# ─── Routers ──────────────────────────────────────────────────────────────────
app.include_router(health_router)

# Placeholder routers (added in Phase 2)
# app.include_router(sessions_router, prefix="/api")
# app.include_router(chat_router, prefix="/api")
# app.include_router(artifacts_router, prefix="/api")


@app.get("/", include_in_schema=False)
async def root():
    return {"message": "Lenny Growth Assistant API", "docs": "/docs", "health": "/health"}
