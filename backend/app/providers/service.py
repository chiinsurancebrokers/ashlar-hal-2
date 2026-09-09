from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

import httpx

from backend.app.core.config import get_settings

REGISTRY_PATH = Path(__file__).resolve().parents[3] / "data" / "providers" / "providers.json"


class _TextExtractor(HTMLParser):
    SKIP = {"script", "style", "noscript", "svg"}
    def __init__(self):
        super().__init__()
        self.parts: list[str] = []
        self.skip_depth = 0
    def handle_starttag(self, tag, attrs):
        if tag.lower() in self.SKIP:
            self.skip_depth += 1
    def handle_endtag(self, tag):
        if tag.lower() in self.SKIP and self.skip_depth:
            self.skip_depth -= 1
    def handle_data(self, data):
        if not self.skip_depth:
            value = " ".join(data.split())
            if value:
                self.parts.append(value)


@dataclass
class SourceSnapshot:
    kind: str
    url: str
    final_url: str
    fetched_at: str
    sha256: str
    text: str
    status: str = "ok"
    error: str | None = None


_CACHE: dict[str, dict] = {}


@lru_cache
def registry() -> dict:
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


def provider_definition(code: str) -> dict:
    item = registry()["providers"].get(code)
    if not item:
        raise KeyError(code)
    return item


def _host_allowed(host: str | None, allowed: list[str]) -> bool:
    return bool(host) and host.lower() in {x.lower() for x in allowed}


def _html_to_text(html: str) -> str:
    parser = _TextExtractor()
    parser.feed(html)
    text = unescape(" ".join(parser.parts))
    return re.sub(r"\s+", " ", text).strip()


async def refresh_provider(code: str) -> dict:
    definition = provider_definition(code)
    allowed = definition["allowed_hosts"]
    snapshots: list[dict] = []

    headers = {
        "User-Agent": "HAL-ProviderKnowledge/2.0 (+Ashlar Assurance; provider information refresh)"
    }

    async with httpx.AsyncClient(timeout=20, follow_redirects=True, headers=headers) as client:
        for source in definition["sources"]:
            url = source["url"]
            parsed = urlparse(url)
            if not _host_allowed(parsed.hostname, allowed):
                snapshots.append(asdict(SourceSnapshot(
                    kind=source["kind"], url=url, final_url=url,
                    fetched_at=datetime.now(timezone.utc).isoformat(),
                    sha256="", text="", status="blocked",
                    error="Source host is not on this provider's allowlist."
                )))
                continue
            try:
                response = await client.get(url)
                response.raise_for_status()
                final_url = str(response.url)
                if not _host_allowed(urlparse(final_url).hostname, allowed):
                    raise RuntimeError("Redirected outside the provider allowlist.")
                text = _html_to_text(response.text)
                # Cap stored text per page for prompt/cost control while keeping useful page context.
                text = text[:18000]
                digest = hashlib.sha256(response.content).hexdigest()
                snapshots.append(asdict(SourceSnapshot(
                    kind=source["kind"], url=url, final_url=final_url,
                    fetched_at=datetime.now(timezone.utc).isoformat(),
                    sha256=digest, text=text
                )))
            except Exception as exc:
                snapshots.append(asdict(SourceSnapshot(
                    kind=source["kind"], url=url, final_url=url,
                    fetched_at=datetime.now(timezone.utc).isoformat(),
                    sha256="", text="", status="error", error=str(exc)[:300]
                )))

    payload = {
        "provider_code": code,
        "name": definition["name"],
        "aliases": definition.get("aliases", []),
        "seed_facts": definition.get("seed_facts", []),
        "refreshed_at": datetime.now(timezone.utc).isoformat(),
        "sources": snapshots,
    }
    _CACHE[code] = payload
    return payload


async def get_provider(code: str, refresh_if_stale: bool = True) -> dict:
    cached = _CACHE.get(code)
    if cached and refresh_if_stale:
        settings = get_settings()
        refreshed = datetime.fromisoformat(cached["refreshed_at"])
        if datetime.now(timezone.utc) - refreshed < timedelta(hours=settings.provider_refresh_hours):
            return cached
    if refresh_if_stale:
        try:
            return await refresh_provider(code)
        except Exception:
            pass
    definition = provider_definition(code)
    return {
        "provider_code": code,
        "name": definition["name"],
        "aliases": definition.get("aliases", []),
        "seed_facts": definition.get("seed_facts", []),
        "refreshed_at": None,
        "sources": [],
    }


async def provider_context(code: str, kinds: set[str] | None = None, char_limit: int = 18000) -> str:
    data = await get_provider(code)
    pieces = [f'Provider: {data["name"]}']
    pieces.extend(f"Verified seed fact: {fact}" for fact in data.get("seed_facts", []))
    used = 0
    for source in data.get("sources", []):
        if source["status"] != "ok":
            continue
        if kinds and source["kind"] not in kinds:
            continue
        chunk = source["text"][:6000]
        used += len(chunk)
        if used > char_limit:
            break
        pieces.append(
            f'Official source ({source["kind"]}) URL: {source["final_url"]}\n'
            f'Fetched: {source["fetched_at"]}\nSHA256: {source["sha256"]}\nCONTENT:\n{chunk}'
        )
    return "\n\n".join(pieces)
