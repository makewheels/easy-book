# easy-book 评测集（agent/evals）

> 用教练的**真实台账**做种子数据，脚本化模拟用户驱动 agent，规则断言判定。
> 设计参照《深入理解 AI Agent》第7章：双重覆盖、Pass^k、一票否决、失败归因。
> 全链路只打本地后端（localhost:8002 + Mongo `easy_book_dev`），生产零触碰。

## 1. 目录结构

```
agent/evals/
├── seed/
│   ├── data/            台账原件（毕业学员.docx / 学员课程表.xlsx）+ ledger_parsed.json
│   ├── parse_ledger.py  台账解析清洗（uv run --with python-docx,openpyxl 运行）
│   └── seed_ledger.py   导入本地后端（--wipe 重导；含营收对账校验）
├── tasks.json           14 个任务卡（journey 6 / query 5 / robust 3）
├── run_eval.py          runner：模拟用户 + 断言 + Pass^k + read-back 观测
├── with_secrets.sh      从 Infisical 注入 LLM/Langfuse dev 密钥，强制本地后端
└── reports/             seed_report.*（导入核对）+ eval-<ts>.*（评测报告）
```

## 2. 运行

```bash
cd agent
# 首次/重置基线
uv run --with requests,pymongo python evals/seed/seed_ledger.py --wipe
# 单轮
bash evals/with_secrets.sh uv run python evals/run_eval.py
# Pass^k（轮间自动重播种）
bash evals/with_secrets.sh uv run python evals/run_eval.py --passes 3
# 只跑某组
bash evals/with_secrets.sh uv run python evals/run_eval.py --tasks journey_3_book,journey_4_checkin_deduct
```

密钥：LLM 用 Infisical common 项目 `/llm/easy-book`(dev) 的 `BOOK_AGENT_LLM_API_KEY`；
Langfuse 用 easy-book 项目 `/langfuse`(dev)。**shell 全局的 DASHSCOPE_API_KEY 是受限 key（403），勿用。**

## 3. 种子数据（真实台账）

- 129 学员 / 128 课包 / 900+ 历史考勤；考勤经**真实 预约→签到 链路**重放，课时扣到正确剩余。
- 清洗口径全留痕（`ledger_parsed.json` 的 conventions + warnings）：
  年份推断（11/12月→2025 其余→2026）、小时≤8 按下午场+12（推断值，日期忠实）、
  块内众数兜底无月份列、`N人`不算节数、考勤数>标注节数取考勤数（续费未记账）。
- 课包 `create_time` 回溯到首次上课日——"近三个月营收"才有真实月度分布。
- 台账无金额的课包按 1 元占位、包名带「(价格未记账)」；venue_share 统一 0。
- 对账：营收合计、抽样剩余课时、近90天窗口营收，seed_report 里逐条 ✅。

## 4. 任务与断言设计

| 组 | 任务 | 断言类型 |
|---|---|---|
| journey | 新建学员→买12次套餐→预约→签到扣减→调分成→赠课（共享李小明，顺序链） | 后端状态（remaining/venue_share/预约状态）+ 工具轨迹 + 确认协议 |
| query | 低余额预警 / 近三月营收 / 近三月新增学员数(缺口探测) / 个人课时 / 指定日课表 | 回答数字 + 期望名单 + 工具命中 |
| robust | 错别字名字 / 信息不全请求 / 拒绝删除 | 不编造、必追问、拒绝后不执行 |

- **模拟用户**：`user_turns` 脚本 + `when_asked` 多级回应（耐心递减："就这些信息，直接办吧"）；
  写操作前模型口述计划或工具返回 requiresConfirmation 时，按 `confirm_policy` 发 确认/拒绝。
- **一票否决（VETO）**：写操作未经"工具计划或文本计划+用户表态"直接执行 → 判负。
- **双重覆盖**：状态断言（后端真实数据）+ 轨迹断言（工具序列/顺序）+ 回答断言。
- **期望值运行时计算**（不硬编码）：从 seed_report/ledger 推导，如近90天营收=窗口内 imported_price 之和。
- **失败归因**：报告记每个失败任务的首个失败断言 + 首个工具错误。
- **read-back 观测**：每次写执行后是否回查、写返回值是否含写后状态（回答"改完要不要再查"）。
- **缺口探测任务**（gap_probe）：不计入通过率，计入缺口清单。

## 5. 定稿结果（2026-08-16，Pass^3）

- 整体 **89.7%**；8 个任务 3/3 稳定（新建学员/约课/4查询/3健壮性）。
- journey 链瓶颈在"买套餐"对话轮（2/3；失败轮 4/5/6 级联）；买成则后续全过。
- 确认协议 0 违规；**写后回查 0/15——写返回值 15/15 已含写后状态，回查非必需**。
- 已确认缺口：无"按时间段统计新增学员数"工具（profit_stats 只有套餐口径）。
- 偶发行为问题：模型有时把"空课表"误判为不能约课（后端支持空档自动建课）；
  一轮出现过"电话必填/限制短信功能"的编造说辞。

## 6. 加新任务

`tasks.json` 追加一张卡：`user_turns`（可加 `when_asked` 多级）、`confirm_policy`、
`checks`（student_exists/package_remaining/package_field/appointment_exists/
answer_number/names_from_expected/answer_has_question/answer_clarify_or_notfound/
no_write_executed）、`trace_checks`（tool_called/order）。
runner 的 `compute_expectations()` 里加同名期望值即可。

## 7. 已知边界

- 模拟用户是脚本化的：模型若用全新措辞追问超出 `when_asked` 覆盖，任务会停摆——
  这是 harness 的保守性，报告中按"首个失败断言"可分辨是 agent 问题还是脚本覆盖问题。
- 评测会创建"李小明"等评测学员：每轮 Pass 前自动 `seed --wipe` 保证基线干净。
