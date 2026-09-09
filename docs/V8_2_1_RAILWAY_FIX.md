# HAL 8.2.1 — Railway dependency fix

The root `requirements.txt` is now self-contained.

Previous:
```text
-r backend/requirements.txt
```

Now the root file directly lists all runtime dependencies, so Railway/Nixpacks
does not depend on a nested requirements file being present after a GitHub upload.

Start command remains:
```text
uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT
```

Healthcheck:
```text
/health
```
