import base64
import json
from typing import Any

import httpx

from .config import settings


class FeishuError(RuntimeError):
    pass


class FeishuClient:
    def __init__(self) -> None:
        self.base = settings.feishu_base_url.rstrip("/")

    async def tenant_access_token(self) -> str:
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.post(
                f"{self.base}/open-apis/auth/v3/tenant_access_token/internal",
                json={
                    "app_id": settings.feishu_app_id,
                    "app_secret": settings.feishu_app_secret,
                },
            )
        data = r.json()
        if r.status_code >= 400 or data.get("code", 0) != 0:
            raise FeishuError(f"tenant_access_token failed: {data}")
        return data["tenant_access_token"]

    async def _headers(self) -> dict[str, str]:
        token = await self.tenant_access_token()
        return {"Authorization": f"Bearer {token}"}

    async def get_record(
        self, app_token: str, table_id: str, record_id: str
    ) -> dict[str, Any]:
        headers = await self._headers()
        url = (
            f"{self.base}/open-apis/bitable/v1/apps/{app_token}"
            f"/tables/{table_id}/records/{record_id}"
        )
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.get(url, headers=headers)
        data = r.json()
        if r.status_code >= 400 or data.get("code", 0) != 0:
            raise FeishuError(f"get_record failed: {data}")
        return data["data"]["record"]

    async def list_fields(
        self, app_token: str, table_id: str
    ) -> list[dict[str, Any]]:
        headers = await self._headers()
        url = (
            f"{self.base}/open-apis/bitable/v1/apps/{app_token}"
            f"/tables/{table_id}/fields"
        )
        items: list[dict[str, Any]] = []
        page_token: str | None = None
        async with httpx.AsyncClient(timeout=30) as client:
            while True:
                params: dict[str, Any] = {"page_size": 100}
                if page_token:
                    params["page_token"] = page_token
                r = await client.get(url, headers=headers, params=params)
                data = r.json()
                if r.status_code >= 400 or data.get("code", 0) != 0:
                    raise FeishuError(f"list_fields failed: {data}")
                page = data["data"]
                items.extend(page.get("items", []))
                if not page.get("has_more"):
                    break
                page_token = page.get("page_token")
        return items

    async def update_record(
        self,
        app_token: str,
        table_id: str,
        record_id: str,
        fields: dict[str, Any],
    ) -> None:
        headers = await self._headers()
        headers["Content-Type"] = "application/json"
        url = (
            f"{self.base}/open-apis/bitable/v1/apps/{app_token}"
            f"/tables/{table_id}/records/{record_id}"
        )
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.put(url, headers=headers, json={"fields": fields})
        data = r.json()
        if r.status_code >= 400 or data.get("code", 0) != 0:
            raise FeishuError(f"update_record failed: {data}")

    async def download_bitable_media(
        self,
        *,
        file_token: str,
        table_id: str,
        record_id: str,
        field_id: str,
    ) -> tuple[bytes, str, str]:
        headers = await self._headers()
        extra = {
            "bitablePerm": {
                "tableId": table_id,
                "attachments": {
                    field_id: {
                        record_id: [file_token],
                    }
                },
            }
        }
        url = f"{self.base}/open-apis/drive/v1/medias/{file_token}/download"
        async with httpx.AsyncClient(timeout=60, follow_redirects=True) as client:
            r = await client.get(
                url,
                headers=headers,
                params={"extra": json.dumps(extra, separators=(",", ":"))},
            )
        if r.status_code >= 400:
            raise FeishuError(
                f"download media failed: HTTP {r.status_code}, {r.text[:300]}"
            )
        content_type = r.headers.get("content-type", "application/octet-stream")
        disposition = r.headers.get("content-disposition", "")
        return r.content, content_type, disposition

    async def upload_qrcode_to_bitable(
        self, *, app_token: str, qrcode_data_url: str
    ) -> str:
        prefix = "data:image/png;base64,"
        if not qrcode_data_url.startswith(prefix):
            raise FeishuError("myaibot qrcode is not a PNG base64 data URL")

        binary = base64.b64decode(qrcode_data_url[len(prefix):])
        headers = await self._headers()
        url = f"{self.base}/open-apis/drive/v1/medias/upload_all"
        form = {
            "file_name": "xhs-publish-qrcode.png",
            "parent_type": "bitable_image",
            "parent_node": app_token,
            "size": str(len(binary)),
        }
        files = {
            "file": ("xhs-publish-qrcode.png", binary, "image/png"),
        }
        async with httpx.AsyncClient(timeout=60) as client:
            r = await client.post(url, headers=headers, data=form, files=files)
        data = r.json()
        if r.status_code >= 400 or data.get("code", 0) != 0:
            raise FeishuError(f"upload qrcode failed: {data}")
        return data["data"]["file_token"]


def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, list):
        parts: list[str] = []
        for item in value:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                if "text" in item:
                    parts.append(str(item["text"]))
                elif "name" in item:
                    parts.append(str(item["name"]))
        return "".join(parts)
    if isinstance(value, dict):
        if "text" in value:
            return str(value["text"])
        if "link" in value:
            return str(value["link"])
    return str(value)


def extract_attachment_tokens(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    out: list[str] = []
    for item in value:
        if isinstance(item, dict):
            token = item.get("file_token") or item.get("fileToken")
            if token:
                out.append(str(token))
    return out
