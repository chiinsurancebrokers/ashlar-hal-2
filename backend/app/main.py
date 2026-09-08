from fastapi import FastAPI
from backend.app.core.config import get_settings
from backend.app.api.carriers import router as carriers_router
from backend.app.api.quotes import router as quotes_router

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="2.0.0-bootstrap",
)

app.include_router(carriers_router, prefix=settings.api_prefix)
app.include_router(quotes_router, prefix=settings.api_prefix)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": settings.app_name,
        "environment": settings.app_env,
    }
