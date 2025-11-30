# 设置Python路径，确保导入当前项目的app模块
import sys
import os

# 添加backend目录到Python路径
backend_path = os.path.dirname(os.path.abspath(__file__))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

# 现在可以安全导入api_server模块
from api_server.main import app

if __name__ == "__main__":
    import uvicorn

    port = 8002 if len(sys.argv) < 2 else int(sys.argv[1])
    uvicorn.run(app, host="0.0.0.0", port=port)
