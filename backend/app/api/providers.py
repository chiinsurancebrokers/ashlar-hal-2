from fastapi import APIRouter, Header, HTTPException

from backend.app.core.config import get_settings
from backend.app.providers.service import get_provider, refresh_provider, registry

router = APIRouter(prefix="/providers", tags=["providers"])


@router.get("")
async def list_providers():
    items=[]
    for code, definition in registry()["providers"].items():
        data=await get_provider(code)
        ok=sum(1 for s in data.get("sources", []) if s.get("status")=="ok")
        items.append({
            "provider_code":code,
            "name":definition["name"],
            "source_count":len(definition["sources"]),
            "sources_available":ok,
            "last_refreshed":data.get("refreshed_at"),
        })
    return {"providers":items}


@router.get("/{provider_code}")
async def provider_profile(provider_code: str):
    try:
        data=await get_provider(provider_code)
    except KeyError:
        raise HTTPException(status_code=404, detail="Unknown provider")
    safe_sources=[]
    for s in data.get("sources", []):
        safe_sources.append({
            "kind":s["kind"], "url":s["url"], "final_url":s["final_url"],
            "fetched_at":s["fetched_at"], "sha256":s["sha256"],
            "status":s["status"], "error":s.get("error"),
        })
    return {
        "provider_code":provider_code,
        "name":data["name"],
        "seed_facts":data.get("seed_facts", []),
        "last_refreshed":data.get("refreshed_at"),
        "sources":safe_sources,
    }


@router.post("/{provider_code}/refresh")
async def provider_refresh(provider_code: str, x_admin_password: str | None = Header(default=None)):
    settings=get_settings()
    if settings.admin_password and x_admin_password != settings.admin_password:
        raise HTTPException(status_code=401, detail="Invalid admin password")
    try:
        data=await refresh_provider(provider_code)
    except KeyError:
        raise HTTPException(status_code=404, detail="Unknown provider")
    return {
        "provider_code":provider_code,
        "refreshed_at":data["refreshed_at"],
        "sources":[{
            "kind":s["kind"],"url":s["url"],"final_url":s["final_url"],
            "fetched_at":s["fetched_at"],"sha256":s["sha256"],"status":s["status"],
            "error":s.get("error")
        } for s in data["sources"]]
    }
