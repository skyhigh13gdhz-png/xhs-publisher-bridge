from typing import Any

import httpx

from .config import settings


class MyaibotError(RuntimeError):
    pass


class MyaibotClient:
    def __init__(self) -> None:
        self.base = settings.myaibot_base_url.rstrip("/")

    async def publish_with_upload(
        self, *, title: str, content: str, images: list[str]
    ) -> dict[str, Any]:
        payload = {
            "api_key": settings.myaibot_api_key,
            "type": "normal",
            "title": title,
            "content": content,
            "images": images,
        }
        async with httpx.AsyncClient(timeout=120) as client:
            r = await client.post(
                f"{self.base}/api/rednote/publish-with-upload",
                json=payload,
            )
        try:
            data = r.json()
        except Exception as exc:
            raise MyaibotError(
                f"myaibot returned non-JSON response: HTTP {r.status_code}"
            ) from exc
        if r.status_code >= 400 or not data.get("success"):
            raise MyaibotError(f"publish failed: {data}")
        return data["data"]

    async def get_status(self, note_id: str) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(
                f"{self.base}/api/rednote/{note_id}/status",
                json={"api_key": settings.myaibot_api_key},
            )
        try:
            data = r.json()
        except Exception as exc:
            raise MyaibotError(
                f"myaibot returned non-JSON response: HTTP {r.status_code}"
            ) from exc
        if r.status_code >= 400 or not data.get("success"):
            raise MyaibotError(f"status failed: {data}")
        return data["data"]
