#!/usr/bin/env bash
# services 机上的 easy-book 部署脚本：构建镜像 → 导入 k3s containerd → apply manifests → 健康检查
# CI 的 deploy job 与手动部署共用。在 /home/ubuntu/easy-book 下执行。
set -euo pipefail

cd "$(dirname "$0")/.."

echo "==> 构建镜像"
docker build -q -t easy-book-backend:latest -f deploy/backend.Dockerfile .
docker build -q -t easy-book-frontend:latest -f deploy/frontend.Dockerfile .
docker build -q -t easy-book-agent:latest -f deploy/agent.Dockerfile .

echo "==> 导入 k3s containerd"
docker save easy-book-backend:latest | sudo k3s ctr -n k8s.io images import -
docker save easy-book-frontend:latest | sudo k3s ctr -n k8s.io images import -
docker save easy-book-agent:latest | sudo k3s ctr -n k8s.io images import -

echo "==> 应用 manifests"
sudo k3s kubectl apply -f deploy/k8s/namespace.yaml

# Secret：合并 deploy/.mongodb-url（MONGODB_URL）与 deploy/.agent-env（LLM/Langfuse 等 KEY=VALUE 行），
# 两个文件均 chmod 600、不入 Git；都不存在则沿用集群中已有 Secret
if [ -f deploy/.mongodb-url ] || [ -f deploy/.agent-env ]; then
  SECRET_ARGS=(--from-literal=DB_NAME=easy_book --from-literal=ENVIRONMENT=production)
  if [ -f deploy/.mongodb-url ]; then
    SECRET_ARGS+=(--from-literal="MONGODB_URL=$(tr -d '\n' < deploy/.mongodb-url)")
  fi
  if [ -f deploy/.agent-env ]; then
    while IFS= read -r line || [ -n "$line" ]; do
      case "$line" in '' | \#*) continue ;; esac
      [ "${line%%=*}" != "$line" ] && SECRET_ARGS+=(--from-literal="$line")
    done < deploy/.agent-env
  fi
  sudo k3s kubectl create secret generic easy-book-config -n easy-book "${SECRET_ARGS[@]}" \
    --dry-run=client -o yaml | sudo k3s kubectl apply -f -
fi

sudo k3s kubectl apply -f deploy/k8s/backend.yaml -f deploy/k8s/frontend.yaml -f deploy/k8s/agent.yaml

echo "==> 滚动重启并等待就绪"
sudo k3s kubectl rollout restart deployment/easy-book-backend deployment/easy-book-frontend deployment/easy-book-agent -n easy-book
sudo k3s kubectl rollout status deployment/easy-book-backend -n easy-book --timeout=180s
sudo k3s kubectl rollout status deployment/easy-book-frontend -n easy-book --timeout=120s
sudo k3s kubectl rollout status deployment/easy-book-agent -n easy-book --timeout=180s

echo "==> 健康检查"
BACKEND_IP=$(sudo k3s kubectl get svc easy-book-backend -n easy-book -o jsonpath='{.spec.clusterIP}')
AGENT_IP=$(sudo k3s kubectl get svc easy-book-agent -n easy-book -o jsonpath='{.spec.clusterIP}')
# 滚动重启后 endpoints 可能短暂抖动，重试 30 秒
for _ in $(seq 1 10); do
  if curl -sf "http://${BACKEND_IP}:8002/health" > /dev/null \
    && curl -sf "http://${AGENT_IP}:8003/ai/" > /dev/null; then
    echo "✅ easy-book 部署完成（backend: ${BACKEND_IP}，agent: ${AGENT_IP}）"
    exit 0
  fi
  sleep 3
done
echo "❌ 健康检查失败" >&2
exit 1
