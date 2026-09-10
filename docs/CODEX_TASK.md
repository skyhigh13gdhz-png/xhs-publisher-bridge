# Codex implementation task

Work from this repository as the baseline. Do not redesign the product.

## Mission

Deliver a verified v0.1 release of the Feishu -> myaibot -> Xiaohongshu QR publishing bridge.

## Required checks before calling it done

1. Install dependencies and run tests.
2. Verify FastAPI starts successfully.
3. Add mocked integration tests for:
   - Feishu record read
   - attachment extraction
   - signed media URL validation
   - myaibot publish success
   - QR upload + record update
   - myaibot error -> Feishu error field
4. Confirm no secret is committed.
5. Keep deployment Docker-based.
6. Do not add a database or frontend in v0.1.
7. Do not replace myaibot with reverse-engineered Xiaohongshu APIs.
8. Treat `submitted` as “Xiaohongshu app launched”, not “published successfully”.

## API contract

Do not break:

- GET /health
- POST /api/v1/publish/from-record
- POST /api/v1/status/sync
- GET /api/v1/media/{file_token}

## Open implementation risks to verify

- Exact Feishu multipart behavior for `drive/v1/medias/upload_all` with `parent_type=bitable_image`.
- Exact `extra` structure required to download attachment media when advanced Bitable permissions are enabled.
- Hyperlink field payload accepted by the user's Base.
- Whether user's Feishu automation can inject current record_id cleanly.

If a real Feishu test disproves an assumption, fix the smallest affected component and document the result. Do not broadly refactor.
