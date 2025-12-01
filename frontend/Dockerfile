# 多阶段构建 - 构建阶段
FROM registry.cn-hangzhou.aliyuncs.com/library/node:18-alpine AS builder

# 设置工作目录
WORKDIR /app

# 复制package文件
COPY package*.json ./

# 安装依赖
RUN npm ci --only=production

# 复制源代码
COPY . .

# 构建应用
RUN npm run build

# 生产阶段 - 使用nginx
FROM registry.cn-hangzhou.aliyuncs.com/library/nginx:alpine