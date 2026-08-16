#!/usr/bin/env bash
# 评测环境注入：LLM 密钥（common 项目 /llm/easy-book dev）+ Langfuse dev 密钥（easy-book 项目 /langfuse）
# 并强制后端指向本地。用法：bash evals/with_secrets.sh uv run python evals/run_eval.py [参数]
set -euo pipefail
LLM_ENV=$(infisical secrets get BOOK_AGENT_LLM_API_KEY -o dotenv \
  --projectId 944d9216-7c11-4174-a39c-d0b339147a99 --path /llm/easy-book --env dev 2>/dev/null)
LF_ENV=$(infisical secrets get LANGFUSE_PUBLIC_KEY LANGFUSE_SECRET_KEY LANGFUSE_HOST -o dotenv \
  --projectId 7663addf-9ca4-44a9-9721-ab135a2fe2dd --path /langfuse --env dev 2>/dev/null)
[ -n "$LLM_ENV" ] || { echo "未取到 LLM 密钥（infisical 登录态？）" >&2; exit 1; }
env $LLM_ENV $LF_ENV EASY_BOOK_API_URL=http://localhost:8002 "$@"
