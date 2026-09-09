# Railway deployment

Keep the Railway service Root Directory set to `/` (repository root).

Nixpacks detects Python from the root-level `requirements.txt`, which delegates to:

    backend/requirements.txt

The included `railway.json` starts HAL with:

    uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT

Healthcheck:

    /health

Do not set Root Directory to `/backend` with this starter unless imports are also
changed from `backend.app...` to `app...`.
