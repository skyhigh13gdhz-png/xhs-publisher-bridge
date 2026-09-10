from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    bridge_token: str
    public_base_url: str
    media_url_ttl_seconds: int = 86400

    myaibot_api_key: str
    myaibot_base_url: str = "https://www.myaibot.vip"

    feishu_app_id: str
    feishu_app_secret: str
    feishu_base_url: str = "https://open.feishu.cn"

    feishu_field_title: str = "标题"
    feishu_field_content: str = "文案"
    feishu_field_images: str = "图片"
    feishu_field_qrcode: str = "二维码"
    feishu_field_link: str = "链接"
    feishu_field_note_id: str = "发布ID"
    feishu_field_status: str = "发布状态"
    feishu_field_error: str = "错误信息"


settings = Settings()
