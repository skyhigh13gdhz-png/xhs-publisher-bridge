import time

from app import security


def test_signed_media_url_contains_signature(monkeypatch):
    monkeypatch.setattr(security.settings, "public_base_url", "https://example.com")
    monkeypatch.setattr(security.settings, "bridge_token", "test-secret")
    monkeypatch.setattr(security.settings, "media_url_ttl_seconds", 60)

    url = security.make_signed_media_url(
        file_token="file1",
        app_token="app1",
        table_id="tbl1",
        record_id="rec1",
        field_id="fld1",
    )
    assert url.startswith("https://example.com/api/v1/media/file1?")
    assert "sig=" in url
    assert "exp=" in url
