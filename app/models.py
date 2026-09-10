from pydantic import BaseModel


class PublishFromRecordRequest(BaseModel):
    app_token: str
    table_id: str
    record_id: str


class SyncStatusRequest(BaseModel):
    app_token: str
    table_id: str
    record_id: str
