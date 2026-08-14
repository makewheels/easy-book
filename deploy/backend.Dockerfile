FROM python:3.12-slim

ENV UV_PYTHON_DOWNLOADS=never

RUN pip install --no-cache-dir -i https://mirrors.aliyun.com/pypi/simple/ uv

WORKDIR /app

COPY backend/pyproject.toml backend/uv.lock ./
# uv.lock 的 source 硬编码了 pypi.org（国内访问极慢）：
# 导出锁定版本清单，改走阿里云镜像安装（版本号仍由 lockfile 钉死）
RUN uv export --frozen --no-dev --no-emit-project --format requirements-txt -o /tmp/requirements.txt \
    && pip install --no-cache-dir -i https://mirrors.aliyun.com/pypi/simple/ -r /tmp/requirements.txt

COPY backend/ ./

EXPOSE 8002

CMD ["python", "run.py"]
