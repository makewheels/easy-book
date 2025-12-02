# Easy Book Docker 部署指南

## 快速部署

### 1. 准备环境

确保服务器已安装：
- Docker (版本 20.10+)
- Docker Compose (版本 1.29+)

### 2. 克隆项目

```bash
git clone <your-repo-url>
cd easy-book
```

### 3. 一键部署

```bash
chmod +x deploy.sh
./deploy.sh
```

### 4. 访问应用

- **前端应用**: http://localhost:80
- **后端API**: http://localhost:8002
- **API文档**: http://localhost:8002/docs

## 手动部署

### 1. 配置环境变量

后端配置文件在 `backend/.env`：
```env
MONGODB_URL=mongodb://admin:easybook123@mongodb:27017/easy_book?authSource=admin
DB_NAME=easy_book
```

### 2. 启动服务

```bash
# 构建并启动所有服务
docker-compose up -d --build

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

### 3. 停止服务

```bash
# 停止并删除容器
docker-compose down

# 停止并删除容器及数据卷
docker-compose down -v
```

## 服务配置

### MongoDB 数据库
- **端口**: 27017
- **管理员账号**: admin / easybook123
- **应用账号**: easybook_user / easybook_pass
- **数据持久化**: 自动创建docker volume

### 后端 API 服务
- **端口**: 8002
- **健康检查**: http://localhost:8002/health
- **自动重启**: 启用
- **工作进程**: 4个

### 前端 Web 服务
- **端口**: 80
- **反向代理**: Nginx
- **静态资源缓存**: 1年
- **Gzip压缩**: 启用

## 常用命令

```bash
# 查看所有容器状态
docker-compose ps

# 查看特定服务日志
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f mongodb

# 重启特定服务
docker-compose restart backend

# 进入容器
docker-compose exec backend bash
docker-compose exec mongodb mongosh

# 备份数据库
docker-compose exec mongodb mongodump --out /backup

# 恢复数据库
docker-compose exec mongodb mongorestore /backup
```

## 生产环境优化

### 1. 修改端口映射

编辑 `docker-compose.yml`，将端口映射改为生产需要的端口：
```yaml
ports:
  - "8080:80"  # 前端改为8080端口
  - "8002:8002"  # 后端保持8002端口
```

### 2. 配置域名和SSL

编辑 `frontend/nginx.conf`，添加域名和SSL配置：
```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    # 其他配置...
}
```

### 3. 数据库备份

设置定时备份：
```bash
# 创建备份脚本
cat > backup.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
docker-compose exec mongodb mongodump --out /backup/$DATE
docker cp $(docker-compose ps -q mongodb):/backup/$DATE ./backups/
EOF

# 添加到crontab
0 2 * * * /path/to/backup.sh
```

## 故障排除

### 1. 容器启动失败
```bash
# 查看详细日志
docker-compose logs [service-name]

# 重新构建镜像
docker-compose build --no-cache [service-name]
```

### 2. 数据库连接失败
```bash
# 检查MongoDB容器状态
docker-compose exec mongodb mongosh --eval "db.adminCommand('ping')"

# 检查网络连接
docker-compose exec backend ping mongodb
```

### 3. 前端无法访问后端
```bash
# 检查代理配置
docker-compose exec frontend nginx -t

# 重启nginx
docker-compose exec frontend nginx -s reload
```

## 安全建议

1. **修改默认密码**: 修改 `docker-compose.yml` 中的MongoDB密码
2. **使用HTTPS**: 在生产环境中配置SSL证书
3. **限制访问**: 使用防火墙限制不必要的端口访问
4. **定期更新**: 保持Docker镜像和依赖库的最新版本
5. **数据备份**: 设置定时数据库备份策略

## 监控和维护

### 健康检查
所有服务都配置了健康检查，可以通过以下命令查看：
```bash
docker-compose ps
```

### 资源监控
```bash
# 查看资源使用情况
docker stats

# 查看磁盘使用
docker system df
```