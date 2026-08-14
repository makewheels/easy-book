FROM python:3.12-slim

RUN pip install --no-cache-dir -i https://mirrors.aliyun.com/pypi/simple/ uv

ENV UV_PYTHON_DOWNLOADS=never

WORKDIR /app

COPY agent/pyproject.toml agent/uv.lock ./
# 依赖 = 主依赖 + langfuse 观测 + web（chainlit）；导出锁定版本后走阿里云镜像安装
RUN uv export --frozen --no-dev --extra langfuse --extra web --no-emit-project --format requirements-txt -o /tmp/requirements.txt \
    && pip install --no-cache-dir -i https://mirrors.aliyun.com/pypi/simple/ -r /tmp/requirements.txt

COPY agent/ ./

EXPOSE 8003

# --root-path /ai：挂在 easybook.a4.fit/ai 子路径下（nginx 保留前缀转发）
CMD ["chainlit", "run", "chainlit_app.py", "--host", "0.0.0.0", "--port", "8003", "--headless", "--root-path", "/ai"]
