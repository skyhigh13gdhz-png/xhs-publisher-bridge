# Ubuntu VPS 部署

## 前提

- Ubuntu VPS
- Docker + Docker Compose
- 一个指向 VPS 的域名
- HTTPS 反向代理（Nginx / Caddy 均可）

不要直接把 8080 端口暴露到公网。

## 启动

```bash
git clone <repo>
cd xhs-publisher-bridge
cp .env.example .env
nano .env
docker compose up -d --build
docker compose logs -f
```

## Nginx 示例

```nginx
server {
    listen 443 ssl http2;
    server_name publish.example.com;

    # ssl_certificate ...
    # ssl_certificate_key ...

    client_max_body_size 40m;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

## 验证

```bash
curl https://publish.example.com/health
```

应返回：

```json
{"status":"ok","version":"0.1.0"}
```

然后再在飞书里触发一条测试记录。
