# Mneme RAG

[![Python](https://img.shields.io/badge/python-%3E%3D3.10-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![LangChain](https://img.shields.io/badge/LangChain-RAG-1C3C3C.svg)](https://python.langchain.com/)

用 **[Mneme](https://github.com/Lucidyn/Mneme)** 做检索，用 **LangChain** 调任意 OpenAI 兼容 LLM 生成回答。  
小而完整：不自建向量库，不引入 Agent——专注 RAG 主路径。

> Mneme（谟涅摩）是本地第二大脑；**生产用法**请直接用 [Mneme 内置问答](https://github.com/Lucidyn/Mneme#llm-配置env)。  
> 本仓库是 **Python / LangChain 接 Mneme API** 的示例与 CLI。

```text
问题
  │
  ▼
Mneme  GET /api/search  (+ 并行 GET /api/chunk)
  │
  ▼
LangChain Prompt → ChatOpenAI(兼容接口) → 回答 + 引用
```

## 功能

| 能力 | 说明 |
|------|------|
| 检索 | 交给 Mneme：关键词 / 语义 / 混合，可选 OCR 与真向量 |
| 生成 | `langchain-openai.ChatOpenAI`，可接 Ollama、vLLM、OneAPI、官方 OpenAI |
| CLI | `health` / `search` / `ask`，支持 `--hits`、`--stream`、`--json` |
| 库 | `from mneme_rag import ask`，也可 `ask_stream` |
| 配置 | `.env` 控制 Mneme 地址、模型、温度、检索模式等 |

## 依赖

1. **[Mneme](https://github.com/Lucidyn/Mneme)** 已索引并在跑（默认 `http://127.0.0.1:8791`）
2. **OpenAI 兼容 LLM**（推荐 [Ollama](https://ollama.com)）

```bash
# 终端 A：Mneme
git clone https://github.com/Lucidyn/Mneme.git && cd Mneme
npm install
npm run index:full   # 或: npx tsx src/cli/main.ts index --root ~/notes --ocr --embed
npm run dev          # http://127.0.0.1:8791

# 终端 B：Ollama（示例）
ollama pull qwen2.5:7b
ollama serve
```

## 安装

```bash
git clone https://github.com/Lucidyn/Mneme-rag.git
cd mneme-rag
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
# 或可编辑安装（得到 mneme-rag 命令）:
# pip install -e .
cp .env.example .env   # 按需改模型名 / 地址
```

## 使用

```bash
source .venv/bin/activate

# 检查 Mneme 与当前配置
python ask.py health
# 等价: python -m mneme_rag health

# 只检索，不调用 LLM
python ask.py search --hits "ONNX CUDAExecutionProvider"
python ask.py search --json --mode keyword "第二大脑"

# 检索 + 回答
python ask.py ask "本地第二大脑怎么索引笔记"
python ask.py ask --hits "ONNX CUDAExecutionProvider 报错怎么办"
python ask.py ask --stream "混合检索和关键词有什么区别"
python ask.py ask --json --limit 4 "如何开启 OCR"
```

### 作为库

```python
from mneme_rag import ask, ask_stream, MnemeClient

result = ask("本地笔记怎么做增量索引？")
print(result.answer)
for hit in result.hits:
    print(hit.path, hit.score)

# 流式
hits, context, tokens = ask_stream("OCR 怎么开？")
print("".join(tokens))

# 自定义客户端
with MnemeClient(base_url="http://127.0.0.1:8791") as client:
    hits = client.search("向量 embedding", mode="semantic", limit=5)
```

更多设计说明见 [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)。

## 配置（`.env`）

| 变量 | 默认 | 含义 |
|------|------|------|
| `MNEME_BASE_URL` | `http://127.0.0.1:8791` | Mneme 服务地址 |
| `LLM_BASE_URL` | `http://127.0.0.1:11434/v1` | OpenAI 兼容 API |
| `LLM_API_KEY` | `ollama` | Ollama 可填任意非空 |
| `LLM_MODEL` | `qwen2.5:7b` | 模型名 |
| `LLM_TEMPERATURE` | `0.2` | 采样温度 |
| `LLM_MAX_TOKENS` | _(空)_ | 最大生成 token；空表示不限制 |
| `SEARCH_MODE` | `hybrid` | `hybrid` / `keyword` / `semantic` |
| `SEARCH_LIMIT` | `6` | 检索条数 |
| `SEARCH_KIND` | `all` | 切片类型过滤（透传 Mneme） |
| `REQUEST_TIMEOUT` | `60` | Mneme HTTP 超时（秒） |

也可用任意兼容网关（vLLM、OneAPI、官方 OpenAI），只要改 `LLM_*`。

## 目录

```text
ask.py                 CLI 入口（薄封装）
pyproject.toml         打包 / 入口脚本 mneme-rag
requirements.txt       依赖钉选入口
mneme_rag/
  __main__.py          python -m mneme_rag
  cli.py               命令行实现
  config.py            环境变量
  mneme_client.py      Mneme HTTP（并行拉 chunk）
  chain.py             LangChain LCEL 链
docs/
  ARCHITECTURE.md      架构与数据流
```

## 说明

- 检索完全交给 Mneme（关键词 + 向量 + OCR），本项目只做编排与生成。
- 用 `langchain-openai.ChatOpenAI` 走兼容接口，本地 / 云端都能接。
- 没有 Agent、没有自建 VectorStore，方便学习或二次集成。
- 许可与 Mneme 一致：[Apache-2.0](LICENSE)。

## 相关

- [Mneme](https://github.com/Lucidyn/Mneme) — 本地索引与检索
- [LangChain](https://python.langchain.com/) — Prompt / Chat 编排
