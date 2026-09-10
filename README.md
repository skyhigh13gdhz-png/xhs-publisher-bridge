# xhs-publisher-bridge

把飞书多维表格中的小红书图文笔记转换成 **myaibot 发布二维码**，再把二维码和发布链接自动写回飞书。

> v0.1.0 目标只有一个：  
> **飞书编辑笔记 → 勾选/触发自动化 → 飞书出现二维码 → 手机扫码 → 拉起小红书完成最终发布。**

## 为什么这样做

不保存小红书 Cookie，不在服务器模拟登录，不逆向小红书私有发布接口。服务器只负责：

1. 读取飞书当前记录；
2. 为飞书附件生成短期签名代理 URL；
3. 调用 myaibot `publish-with-upload`；
4. 把二维码、发布链接、发布 ID 和状态写回飞书。

最终账号身份仍由手机上当前登录的小红书 App 决定。

## v0.1.0 飞书字段

默认字段名：

| 字段 | 类型 | 用途 |
|---|---|---|
| 标题 | 文本 | 小红书标题 |
| 文案 | 多行文本 | 正文 |
| 图片 | 附件 | 1–18 张图片 |
| 二维码 | 附件 | 服务自动写回 |
| 链接 | 超链接 | 服务自动写回 |
| 发布ID | 文本 | myaibot note id |
| 发布状态 | 单选 | 生成中 / 待扫码 / 已拉起小红书 / 生成失败 |
| 错误信息 | 多行文本 | 出错时写回 |

字段名都能通过 `.env` 修改。

## API

### 健康检查

`GET /health`

### 从飞书记录生成二维码

`POST /api/v1/publish/from-record`

Header:

`Authorization: Bearer <BRIDGE_TOKEN>`

Body:

```json
{
  "app_token": "bascnxxxx",
  "table_id": "tblxxxx",
  "record_id": "recxxxx"
}
```

### 同步扫码/拉起状态

`POST /api/v1/status/sync`

Body 与上面相同。

> `已拉起小红书` 不等于最终发布成功。myaibot 的 `submitted` 只表示用户点击了发布并拉起小红书。

## 本地启动

```bash
cp .env.example .env
# 填好配置
docker compose up -d --build
curl http://127.0.0.1:8080/health
```

线上必须放在 HTTPS 反向代理之后，例如：

`https://publish.your-domain.com`

然后设置：

`PUBLIC_BASE_URL=https://publish.your-domain.com`

## 关键安全点

- `MYAIBOT_API_KEY`、`FEISHU_APP_SECRET`、`BRIDGE_TOKEN` 只放服务器 `.env`。
- 飞书附件不会永久公开；桥接器生成带 HMAC 签名和过期时间的临时代理地址。
- 不保存小红书账号 Cookie。
- 不把 myaibot API Key 下发到浏览器或飞书表格。
