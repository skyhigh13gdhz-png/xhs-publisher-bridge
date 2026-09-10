import hashlib
import hmac
import time
from urllib.parse import urlencode

from fastapi import Header, HTTPException

from .config import settings


def require_bridge_token(authorization: str | None = Header(default=None)) -> None:
    expected = f"Bearer {settings.bridge_token}"
    if not authorization or not hmac.compare_digest(authorization, expected):
        raise HTTPException(status_code=401, detail="Unauthorized")


def _media_signature(payload: str) -> str:
    return hmac.new(
        settings.bridge_token.encode(),
        payload.encode(),
        hashlib.sha256,
    ).hexdigest()


def make_signed_media_url(
    *,
    file_token: str,
    app_token: str,
    table_id: str,
    record_id: str,
    field_id: str,
) -> str:
    exp = int(time.time()) + settings.media_url_ttl_seconds
    values = {
        "app_token": app_token,
        "table_id": table_id,
        "record_id": record_id,
        "field_id": field_id,
        "exp": str(exp),
    }
    canonical = "|".join(
        [
            file_token,
            values["app_token"],
            values["table_id"],
            values["record_id"],
            values["field_id"],
            values["exp"],
        ]
    )
    values["sig"] = _media_signature(canonical)
    return (
        f"{settings.public_base_url.rstrip('/')}/api/v1/media/{file_token}"
        f"?{urlencode(values)}"
    )


def verify_media_signature(
    *,
    file_token: str,
    app_token: str,
    table_id: str,
    record_id: str,
    field_id: str,
    exp: int,
    sig: str,
) -> None:
    if exp < int(time.time()):
        raise HTTPException(status_code=410, detail="Media URL expired")

    canonical = "|".join(
        [file_token, app_token, table_id, record_id, field_id, str(exp)]
    )
    expected = _media_signature(canonical)
    if not hmac.compare_digest(sig, expected):
        raise HTTPException(status_code=403, detail="Invalid media signature")
