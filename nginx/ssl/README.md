# Nginx SSL 证书说明

生产环境需要配置 SSL 证书以支持 HTTPS 访问。

## 证书文件

将以下文件放置在此目录：
- `cert.pem` - SSL 证书文件
- `key.pem` - 私钥文件

## 获取证书

### 方式一：使用 Let's Encrypt 免费证书

```bash
# 安装 certbot
apt-get install certbot python3-certbot-nginx

# 获取证书
certbot --nginx -d yourdomain.com

# 证书会自动安装到 nginx 配置
```

### 方式二：购买商业证书

从阿里云、腾讯云等云服务商购买 SSL 证书，下载证书文件后放置在此目录。

### 方式三：开发环境使用自签名证书

```bash
# 生成自签名证书（仅用于开发测试）
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout key.pem -out cert.pem \
  -subj "/C=CN/ST=Beijing/L=Beijing/O=Dev/CN=localhost"
```

## 注意事项

- 证书文件应设置适当的权限（600）
- 生产环境请勿使用自签名证书
- 定期更新证书（Let's Encrypt 证书有效期为 90 天）
