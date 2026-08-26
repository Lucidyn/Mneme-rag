# Architecture

Mneme RAG 是 Mneme 的问答编排层：检索在 Mneme，生成在本仓库。

## 数据流

```text
┌─────────────┐     GET /api/search      ┌──────────────┐
│  CLI / 库   │ ───────────────────────► │    Mneme     │
│  ask(...)   │     GET /api/chunk ×N    │  (索引+检索)  │
└──────┬──────┘ ◄─────────────────────── └──────────────┘
       │              hits + full text
       ▼
┌─────────────┐
│ format_context │  → 编号块 [1] path:line …
└──────┬──────┘
       ▼
┌─────────────┐     OpenAI-compatible      ┌──────────────┐
│ ChatPrompt  │ ─────────────────────────► │ Ollama/vLLM/ │
│ + ChatOpenAI│ ◄───────────────────────── │ OpenAI …     │
└──────┬──────┘         answer tokens      └──────────────┘
       ▼
   AskResult(answer, hits, context)
```

## 模块职责

| 模块 | 职责 |
|------|------|
| `config.Settings` | 从 `.env` / 环境变量读配置（不可变 dataclass） |
| `mneme_client.MnemeClient` | `health` / `search` / `chunk`；并行拉取 chunk 全文 |
| `mneme_client.format_context` | 把 hits 拼成带编号的 prompt 上下文 |
| `chain.ask` / `ask_stream` | 检索 → Prompt → LLM；流式版本先返回 hits 再 yield token |
| `cli` | `health` / `search` / `ask` 子命令 |

## 为何不自建向量库

Mneme 已负责：

- 文件遍历与切片
- MiniSearch 关键词
- 可选句向量 embedding + 混合排序
- 可选 OCR

本仓库只消费 HTTP API，避免重复索引与双份模型缓存。

## 检索增强细节

1. `GET /api/search` 返回命中（含 `snippet`、`score`、`source`）。
2. 对每个 hit 并行 `GET /api/chunk?id=`，用全文替换 snippet，提高生成质量。
3. 上下文块格式：

```text
[1] path/to/file.md:12 · Heading
来源=hybrid score=0.842 kind=text
<body>
```

4. System prompt 要求：只依据上下文作答，文末「参考：」列出编号与路径。

## LLM 适配

`ChatOpenAI(base_url=…, api_key=…, model=…)` 兼容：

- Ollama：`http://127.0.0.1:11434/v1`
- vLLM / LocalAI / OneAPI / 官方 OpenAI

温度与 `max_tokens` 由 `LLM_TEMPERATURE` / `LLM_MAX_TOKENS` 控制。

## 扩展建议

- **多轮对话**：在 CLI 外维护 `ChatPromptTemplate` 历史，每轮仍先检索再答。
- **引用深链**：命中含 `path` + `start_line`，可拼 Cursor / VS Code `file://` 或 Mneme 打开 API。
- **评测**：用固定问题集对比 `keyword` / `semantic` / `hybrid` 的 hit 质量与答案忠实度。
- **不要**：在本仓库再嵌一套 embedding；需要改检索策略时改 Mneme 或传 `mode` / `kind` / `limit`。
