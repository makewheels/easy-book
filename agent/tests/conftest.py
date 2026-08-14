"""测试环境统一关闭 Langfuse 上报，避免离线测试的 span 污染 dev/prod project。

必须在任何 book_agent 模块导入前生效：置空 LANGFUSE_SECRET_KEY 后，
config 的 .env 加载不会覆盖已存在的键，trace 层整体 no-op。
"""

import os

os.environ["LANGFUSE_SECRET_KEY"] = ""
