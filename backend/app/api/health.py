from fastapi import APIRouter
from app.config import settings
from app.models.schemas import HealthResponse
import httpx
import structlog

logger = structlog.get_logger()
router = APIRouter()


async def check_database() -> str:
    try:
        from app.database import get_engine
        from sqlalchemy import text
        async with get_engine().connect() as conn:
            await conn.execute(text("SELECT 1"))
        return "connected"
    except Exception as e:
        logger.warning("health.db_check_failed", error=str(e))
        return "unavailable"


async def check_ollama() -> str:
    if settings.llm_provider != "ollama":
        return "not_configured"
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(f"{settings.ollama_base_url}/api/tags")
            if resp.status_code == 200:
                return "connected"
            return f"error_{resp.status_code}"
    except Exception:
        return "unavailable"


async def check_anthropic() -> str:
    if settings.llm_provider != "anthropic":
        return "not_configured"
    return "configured" if settings.anthropic_api_key else "missing_key"


@router.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Primary health check — returns status of all dependencies."""
    db_status = await check_database()
    
    if settings.llm_provider == "ollama":
        llm_status = await check_ollama()
        model = settings.ollama_model
    else:
        llm_status = await check_anthropic()
        model = "claude-3-5-haiku-20241022"

    return HealthResponse(
        status="ok",
        environment=settings.environment,
        llm_provider=f"{settings.llm_provider} ({llm_status})",
        llm_model=model,
        database=db_status,
        vector_store="chromadb",
    )


@router.get("/health/model", tags=["Health"])
async def model_health():
    """Check if the configured LLM is reachable and responding."""
    if settings.llm_provider == "ollama":
        status = await check_ollama()
        return {"provider": "ollama", "model": settings.ollama_model, "status": status}
    else:
        status = await check_anthropic()
        return {"provider": "anthropic", "model": "claude-3-5-haiku-20241022", "status": status}
