# book-agent — Easy-Book 自然语言助手

用自然语言操作泳课管理系统：查明天的课、给学员加课时、买课包、约课、签到、统计利润。

工具层与 agent loop 的组织方式参考 [video-2022](https://github.com/makewheels/video-2022) 的
`ai-agent/` 包：schema 与执行分离、方法名即工具名、写确认协议、错误转返回值。

## 快速开始

```powershell
cd agent
uv sync                              # 安装依赖
copy .env.example .env               # 填入 LLM API key

# 检查后端连通性（需先启动 backend）
uv run book-agent health

# 单轮问答
uv run book-agent ask "明天有什么课程？"
uv run book-agent ask "给张小明加 5 节课"        # 写操作会先要求确认
uv run book-agent ask "这个月利润多少？"

# 交互式多轮对话
uv run book-agent chat

# 打印全部工具 schema（JSON，供其他 agent 框架接入）
uv run book-agent tools
```

## 配置（agent/.env）

| 变量 | 默认值 | 说明 |
|---|---|---|
| `BOOK_AGENT_LLM_API_KEY` | — | LLM key（也读 `DASHSCOPE_API_KEY` / `OPENAI_API_KEY`） |
| `BOOK_AGENT_LLM_BASE_URL` | DashScope 兼容端点 | 任意 OpenAI 兼容 `/chat/completions` |
| `BOOK_AGENT_LLM_MODEL` | `qwen-plus` | 模型 id |
| `EASY_BOOK_API_URL` | `http://localhost:8002` | easy-book 后端地址 |
| `BOOK_AGENT_CONFIRM_WRITE` | `false` | `true` 时写操作免确认（慎用） |

## 架构

```
book_agent/
├── schema.py     # ALL_TOOLS：20 个工具的 OpenAI function schema（description 是操作手册）
├── tools.py      # BookTools：方法名即工具名，execute() getattr 分发
├── client.py     # OpenAI 兼容 LLM 客户端（urllib，零额外依赖）
├── assistant.py  # SYSTEM_PROMPT + 手写 agent loop（最多 8 轮）
├── config.py     # 环境变量配置
└── __main__.py   # CLI：ask / chat / tools / health

tests/
├── test_contract.py      # 契约测试：schema ↔ 方法签名逐工具对齐（离线）
├── test_tools_offline.py # 写确认协议、未知工具、错误转返回值（离线）
└── test_tools_live.py    # 全流程 live 测试（后端不在线自动 skip）
```

### 核心约定（同 video-2022）

1. **新增工具 = 两处对齐**：`schema.py` 加一条 schema + `tools.py` 加一个同名方法，
   契约测试会钉死两边一致。
2. **写确认**：`WRITE_TOOLS` 里的工具默认返回 `{"requiresConfirmation": True, "planned": {...}}`，
   agent 会先转述计划征求用户同意。
3. **错误即返回值**：`execute()` 捕获一切异常转成 `{"error": "..."}`，让模型自行纠错，
   永不炸掉 agent loop。
4. **先查再改**：系统提示词要求模型先用 search/list 工具拿到真实 id，禁止编造。

## 工具清单（20 个）

查询（9）：`search_students` `get_student` `get_schedule` `get_schedule_range`
`list_student_appointments` `list_student_packages` `get_package` `profit_stats` `lessons_overview`

写操作（11，需确认）：`create_student` `update_student` `delete_student`
`create_package` `update_package` `adjust_package_lessons` `delete_package`
`book_appointment` `cancel_appointment` `checkin_appointment` `set_appointment_status`

## 运行测试

```powershell
uv run pytest tests -v     # live 用例需要后端在 localhost:8002，否则自动跳过
```
