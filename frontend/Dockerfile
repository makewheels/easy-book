# 多阶段构建 - 构建阶段
FROM node:18-alpine as build-stage

WORKDIR /app

# 复制package文件
COPY package*.json ./

# 安装依赖
RUN npm install

# 复制源代码
COPY . .

# 构建应用
RUN npm run build

# 生产阶段 - 使用简单的HTTP服务器
FROM node:18-alpine as production-stage

WORKDIR /app

# 复制构建结果
COPY --from=build-stage /app/dist ./dist

# 安装serve来托管静态文件
RUN npm install -g serve

# 暴露端口
EXPOSE 80

# 启动静态文件服务器
CMD ["serve", "-s", "dist", "-l", "80"]