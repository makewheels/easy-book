#!/usr/bin/env bash
# services 机上的 easy-book 部署脚本：构建镜像 → 导入 k3s containerd → apply manifests → 健康检查
# CI 的 deploy job 与手动部署共用。在 /home/ubuntu/easy-book 下执行。
set -euo pipefail

cd "$(dirname "$0")/.."

echo "==> 构建镜像"
docker build -q -t easy-book-backend:latest -f deploy/backend.Dockerfile .
docker build -q -t easy-book-frontend:latest -f deploy/frontend.Dockerfile .

echo "==> 导入 k3s containerd"
docker save easy-book-backend:latest | sudo k3s ctr -n k8s.io images import -
docker save easy-book-frontend:latest | sudo k3s ctr -n k8s.io images import -

echo "==> 应用 manifests"
sudo k3s kubectl apply -f deploy/k8s/namespace.yaml

# Secret：从 deploy/.mongodb-url 读取（chmod 600，不入 Git）；文件不存在则沿用集群中已有 Secret
if [ -f deploy/.mongodb-url ]; then
  sudo k3s kubectl create secret generic easy-book-config -n easy-book \
    --from-literal=MONGODB_URL="$(tr -d '\n' < deploy/.mongodb-url)" \
    --from-literal=DB_NAME=easy_book \
    --from-literal=ENVIRONMENT=production \
    --dry-run=client -o yaml | sudo k3s kubectl apply -f -
fi

sudo k3s kubectl apply -f deploy/k8s/backend.yaml -f deploy/k8s/frontend.yaml

echo "==> 滚动重启并等待就绪"
sudo k3s kubectl rollout restart deployment/easy-book-backend deployment/easy-book-frontend -n easy-book
sudo k3s kubectl rollout status deployment/easy-book-backend -n easy-book --timeout=180s
sudo k3s kubectl rollout status deployment/easy-book-frontend -n easy-book --timeout=120s

echo "==> 健康检查"
BACKEND_IP=$(sudo k3s kubectl get svc easy-book-backend -n easy-book -o jsonpath='{.spec.clusterIP}')
# 滚动重启后 endpoints 可能短暂抖动，重试 30 秒
for _ in $(seq 1 10); do
  if curl -sf "http://${BACKEND_IP}:8002/health" > /dev/null; then
    echo "✅ easy-book 部署完成（backend ClusterIP: ${BACKEND_IP}）"
    exit 0
  fi
  sleep 3
done
echo "❌ 健康检查失败" >&2
exit 1
