# AI 助手：建议问题与用户记忆

> 让教练"少打字、被记住"：开场/跟进建议按钮 + 分类型长期记忆。
> 2026-08-16 上线（本地验证通过），涉及 backend / agent / deploy 三处。

## 1. 总体架构

```
教练浏览器 ──eb_token──▶ nginx(前端容器)
                          │ auth_request /api/auth/check
                          │   └─ 200 + X-User-Id(手机号)   ← auth.py check_session 带出
                          │ auth_request_set + proxy_set_header X-User-Id
                          ▼
                     Chainlit(/ai)  chainlit_app.py
                          │ 读 session.environ["HTTP_X_USER_ID"] 得到 user_id
                          │ 开场建议  GET  /api/agent/suggestions      （状态驱动，无身份也可用）
                          │ 每轮回答后 GET /api/agent/suggestions?user_id= （个性化排序）
                          │ 提问落库  POST /api/agent/queries
                          │ 记忆读写  GET/POST /api/agent/memories
                          ▼
                     backend(8002)  api/agent.py + services/suggestions.py
                          │ Mongo: agent_queries / agent_memory
```

生产鉴权下 agent→backend 走 `X-Service-Key`（`EASY_BOOK_SERVICE_KEY`，见
`deploy/k8s/secret.example.yaml` 同类机制）；本地 dev 鉴权关闭直通。
所有后端调用失败都**静默降级**（建议退回静态兜底、记忆不注入），聊天主链路不受影响。

## 2. 建议问题（suggestions）

### 2.1 候选来源（纯 DB 查询，零 LLM 成本）

| 意图 intent | 触发条件 | 示例 message | 基础分 |
|---|---|---|---|
| low_balance | 有学员剩余课时 ≤3 | 「傅思琪只剩1节课了，还有其他10位学员课时不多，看看续课建议」 | 90 |
| today_checkin | 今天有预约 | 「今天有什么课？上完的帮我签到」 | 80 |
| monthly_profit | 总是候选；**每月前7天**基础分上浮到 85 | 「这个月收入多少？」 | 60/85 |
| no_package | 有学员没有课包 | 「冯文钰还没有课包，帮ta买一个」 | 55 |
| lessons_overview / tomorrow_schedule / new_student | 兜底 | 静态三条 | 50/45/40 |

### 2.2 个性化排序

`score = base + 8 * min(该用户该意图历史次数, 5)`，次数来自 `agent_queries`
（Chainlit 每轮回答后把 用户/原文/意图/工具 落库；意图由命中的工具映射，见
`chainlit_app.INTENT_BY_TOOL`）。取 score 前 N（默认 3，message 去重）。

### 2.3 展示位置（Chainlit 行为约束）

- **开场**：`@cl.set_starters` 动态拉取。注意 Chainlit 的 starters **只在空会话显示**，
  因此 `on_chat_start` **不再发开场问候**（发了就隐藏建议按钮）。
- **每轮回答后**：回答消息挂 3 个 `cl.Action` 按钮（`suggest_question`），
  点击 = 以该问题发起新一轮对话（`@cl.action_callback`）。这里有 user_id，是个性化生效的地方。

## 3. 用户记忆（agent_memory）

### 3.1 记忆类型（kind）与实用场景

| kind | 含义 | 例子 | 生效方式 |
|---|---|---|---|
| preference | 偏好习惯 | 新课包默认1对1/12节/1600；回答简洁点 | 注入系统提示词，买课包少追问 |
| fact | 业务事实 | 俱乐部分成一般600；冬天改下午3点开课 | 回答/操作自动带规则 |
| person | 学员相关 | 小红是张钰桐的小名；李家姐妹一起上课 | 说小名也能认人 |
| process | 未完成事项 | 曹赫的分成调整还没办 | 下次主动提醒跟进 |
| pattern | 时间规律 | 教练月初会查营收 | 建议排序/主动提示 |

### 3.2 写入路径（三条）

1. **工具显式记录**：`save_user_memory(kind, content)`（第 21 个工具，走两步确认协议——
   教练能看到"我将记住什么"再同意）。source=`user_explicit`，confidence=0.9。
2. **会话结束 LLM 抽取**：`@cl.on_chat_end` 用同一模型（temperature=0）对最近对话
   抽 ≤5 条候选记忆。source=`llm_extract`，confidence=0.6。抽取失败静默忽略。
3. **行为统计**（不写 agent_memory）：`agent_queries` 的意图计数直接用于建议排序。

### 3.3 读取路径

- **系统提示词注入**：`on_chat_start` 拉该用户 active 记忆前 15 条，拼成
  「## 你对这位教练的记忆」段落，经 `BookAssistant(extra_system=...)` 追加到系统提示词末尾；
  并提示"与实时查询冲突时以查询为准"。
- **建议排序**：见 2.2。

### 3.4 生命周期与治理

- 去重：同 user+kind+content 只提升 confidence/更新时间，不重复插入。
- 上限：每用户 active ≤200 条，超出软删最旧（`status=deleted`，保留可审计）。
- 删除：`DELETE /api/agent/memories/{id}` 软删。
- 身份：user_id = 手机号（nginx 透传）；本地/无身份时为空串=全局记忆。

## 4. 接口清单（backend `api/agent.py`，均挂 require_auth）

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | /api/agent/suggestions?user_id=&limit= | 建议列表（score 降序） |
| POST | /api/agent/queries | 提问记录 {user_id,text,intent,tools} |
| GET | /api/agent/memories?user_id= | 有效记忆列表 |
| POST | /api/agent/memories | 创建/去重更新 |
| DELETE | /api/agent/memories/{id} | 软删 |

## 5. 部署与降级

- nginx：`deploy/frontend-nginx.conf` 的 `/ai` location 增加
  `auth_request_set $auth_user_id $upstream_http_x_user_id; proxy_set_header X-User-Id ...`。
- 无 X-User-Id（本地/旧前端配置）→ 建议不个性化、记忆走全局；功能不坏。
- backend 不可达 → starters 退回 `FALLBACK_STARTERS`，聊天正常。

## 6. 本地运行注意

- agent 项目钉 **Python 3.12**（`agent/.python-version`，与 `deploy/agent.Dockerfile` 一致）。
  Python 3.14 下 chainlit 依赖的 nest-asyncio 与 sniffio 不兼容，静态资源 500、页面白屏。
- 起服务：`bash evals/with_secrets.sh uv run chainlit run chainlit_app.py --port 8003 --headless`
  （脚本注入 LLM/Langfuse dev 密钥并指向本地后端）。

## 7. 扩展指引

- 加建议候选：`services/suggestions.py::_state_candidates` 加一条 + `BASE_SCORE` 权重。
- 加记忆类型：`api/agent.py MEMORY_KINDS` + `schema/memory.py` 的 enum + 本文档表格。
- 评测：建议/记忆接口已有单测（`backend/tests/unit/test_agent_suggestions.py`）；
  端到端回归见 `docs/eval-suite.md`。
