# Examples

## 1. 健康检查

```bash
python -m mneme_rag health
```

期望看到 `indexed: True` 以及 `files` / `chunks` 非空。若 Mneme 未启动会打印不可达错误。

## 2. 只检索

```bash
python -m mneme_rag search --mode hybrid --limit 5 "增量索引"
python -m mneme_rag search --json "OCR"
```

## 3. 问答并查看命中

```bash
python -m mneme_rag ask --hits "本地第二大脑怎么索引笔记"
```

## 4. 流式输出

```bash
python -m mneme_rag ask --stream "混合检索适合什么问题"
```

## 5. Python 调用

```python
from mneme_rag import ask

r = ask("图片能不能被检索到？", mode="hybrid", limit=4)
print(r.answer)
print([h.path for h in r.hits])
```

## 6. 换模型

`.env`：

```env
LLM_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=sk-...
LLM_MODEL=gpt-4o-mini
```

或本地 vLLM：

```env
LLM_BASE_URL=http://127.0.0.1:8000/v1
LLM_API_KEY=EMPTY
LLM_MODEL=Qwen/Qwen2.5-7B-Instruct
```
