from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.responses import Response

from .config import settings
from .feishu import (
    FeishuClient,
    FeishuError,
    extract_attachment_tokens,
    normalize_text,
)
from .models import PublishFromRecordRequest, SyncStatusRequest
from .myaibot import MyaibotClient, MyaibotError
from .security import (
    make_signed_media_url,
    require_bridge_token,
    verify_media_signature,
)

app = FastAPI(title="XHS Publisher Bridge", version="0.1.0")
feishu = FeishuClient()
myaibot = MyaibotClient()


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "version": "0.1.0"}


@app.get("/api/v1/media/{file_token}")
async def proxy_media(
    file_token: str,
    app_token: str = Query(...),
    table_id: str = Query(...),
    record_id: str = Query(...),
    field_id: str = Query(...),
    exp: int = Query(...),
    sig: str = Query(...),
) -> Response:
    verify_media_signature(
        file_token=file_token,
        app_token=app_token,
        table_id=table_id,
        record_id=record_id,
        field_id=field_id,
        exp=exp,
        sig=sig,
    )
    try:
        content, content_type, disposition = await feishu.download_bitable_media(
            file_token=file_token,
            table_id=table_id,
            record_id=record_id,
            field_id=field_id,
        )
    except FeishuError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    headers = {}
    if disposition:
        headers["Content-Disposition"] = disposition
    return Response(content=content, media_type=content_type, headers=headers)


@app.post(
    "/api/v1/publish/from-record",
    dependencies=[Depends(require_bridge_token)],
)
async def publish_from_record(req: PublishFromRecordRequest) -> dict[str, Any]:
    try:
        record = await feishu.get_record(req.app_token, req.table_id, req.record_id)
        fields = record.get("fields", {})

        title = normalize_text(fields.get(settings.feishu_field_title)).strip()
        content = normalize_text(fields.get(settings.feishu_field_content)).strip()
        attachments = extract_attachment_tokens(
            fields.get(settings.feishu_field_images)
        )

        if not attachments:
            raise HTTPException(
                status_code=400,
                detail=f"Field '{settings.feishu_field_images}' has no attachments",
            )

        table_fields = await feishu.list_fields(req.app_token, req.table_id)
        field_map = {
            str(item.get("field_name")): str(item.get("field_id"))
            for item in table_fields
        }
        image_field_id = field_map.get(settings.feishu_field_images)
        if not image_field_id:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot find field id for '{settings.feishu_field_images}'",
            )

        await _safe_set_status(
            req, "生成中", error=""
        )

        image_urls = [
            make_signed_media_url(
                file_token=file_token,
                app_token=req.app_token,
                table_id=req.table_id,
                record_id=req.record_id,
                field_id=image_field_id,
            )
            for file_token in attachments
        ]

        result = await myaibot.publish_with_upload(
            title=title,
            content=content,
            images=image_urls,
        )

        note_id = str(result["id"])
        publish_url = str(result["url"])
        qrcode_data_url = str(result["qrcode"])
        qr_file_token = await feishu.upload_qrcode_to_bitable(
            app_token=req.app_token,
            qrcode_data_url=qrcode_data_url,
        )

        update_fields: dict[str, Any] = {
            settings.feishu_field_qrcode: [{"file_token": qr_file_token}],
            settings.feishu_field_link: {
                "text": "手机扫码发布",
                "link": publish_url,
            },
            settings.feishu_field_note_id: note_id,
            settings.feishu_field_status: "待扫码",
            settings.feishu_field_error: "",
        }
        await feishu.update_record(
            req.app_token,
            req.table_id,
            req.record_id,
            update_fields,
        )

        return {
            "success": True,
            "record_id": req.record_id,
            "note_id": note_id,
            "url": publish_url,
            "status": "pending",
        }

    except HTTPException:
        raise
    except (FeishuError, MyaibotError, KeyError, ValueError) as exc:
        await _safe_set_status(req, "生成失败", error=str(exc)[:1000])
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.post(
    "/api/v1/status/sync",
    dependencies=[Depends(require_bridge_token)],
)
async def sync_status(req: SyncStatusRequest) -> dict[str, Any]:
    try:
        record = await feishu.get_record(req.app_token, req.table_id, req.record_id)
        fields = record.get("fields", {})
        note_id = normalize_text(fields.get(settings.feishu_field_note_id)).strip()
        if not note_id:
            raise HTTPException(status_code=400, detail="No 发布ID in this record")

        status_data = await myaibot.get_status(note_id)
        raw = status_data.get("status", "")
        mapped = {
            "uploading": "素材处理中",
            "pending": "待扫码",
            "submitted": "已拉起小红书",
        }.get(raw, raw or "未知")

        await feishu.update_record(
            req.app_token,
            req.table_id,
            req.record_id,
            {
                settings.feishu_field_status: mapped,
                settings.feishu_field_error: "",
            },
        )
        return {
            "success": True,
            "note_id": note_id,
            "status": raw,
            "status_label": mapped,
            "status_meaning": status_data.get("status_meaning"),
        }
    except HTTPException:
        raise
    except (FeishuError, MyaibotError, KeyError, ValueError) as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


async def _safe_set_status(
    req: PublishFromRecordRequest | SyncStatusRequest,
    status: str,
    *,
    error: str,
) -> None:
    try:
        await feishu.update_record(
            req.app_token,
            req.table_id,
            req.record_id,
            {
                settings.feishu_field_status: status,
                settings.feishu_field_error: error,
            },
        )
    except Exception:
        # Status reporting must never mask the original publish error.
        pass
