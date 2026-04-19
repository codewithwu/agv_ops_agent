# AGV RAG 向量存储方案

## 选型

**向量存储**：PGVector

LangChain 使用 `PGVectorStore`，底层是 PostgreSQL 的 `pgvector` 扩展。

## RAG 流程

```
上传文件 → PyPDFLoader 加载 → RecursiveCharacterTextSplitter 分割 → PGVector 存储
```

```python
# 1. 加载 PDF
loader = PyPDFLoader("xxx.pdf")
docs = loader.load()

# 2. 分割
splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
chunks = splitter.split_documents(docs)

# 3. 存入向量库
vector_store.add_documents(chunks)
```

## 关键说明

### add_documents 耗时分析

`add_documents` 是一个**耗时操作**，主要瓶颈在 Embedding API 调用：

```python
def add_documents(self, file_path, metadata=None):
    # 步骤1: 加载+分割（较快，~100ms）
    result = self._doc_processor.process_file(file_path, metadata)

    # 步骤2: 存入向量库（主要耗时）
    return self._get_vectorstore().add_documents(result.documents)
    # - 对每个chunk调用 embed_query() → HTTP请求到Ollama/ModelScope ⚠️
    # - 插入向量到PostgreSQL（较快，~50ms）
```

假设文档被分割成 10 个 chunk：

| 步骤 | 耗时 | 说明 |
|------|------|------|
| 加载+分割 | ~100ms | 文件IO+文本处理 |
| Embedding API × 10 | ~1-5s | **主要瓶颈**，每个chunk一次HTTP请求 |
| 数据库插入 × 10 | ~50ms | 较快 |

**优化方向**：将 Embedding 请求并发化（用 `asyncio.gather`），10 个 chunk 的 embedding 时间从 ~10s 降到 ~1-2s。

### LangChain 自动管理向量表
PGVector 会自动创建 `langchain_pg_embedding` 表，包含：
- id (uuid)
- collection_id
- embedding (vector)
- document (text content)
- custom_id

**不需要额外创建 Document 模型**。

### 向量检索准确性
向量检索基于语义相似度，不相关文档得分低，不会混淆。

### 检索速度
PGVector 有索引（IVFFlat/HNSW）加速：
| 数据量 | 检索速度 |
|--------|----------|
| 1万条 | <10ms |
| 10万条 | <50ms |
| 100万条 | <200ms |

### 权限控制
使用同一个 collection，通过 metadata 过滤：

- 存储时：`user_id` 存入 document metadata
- 查询时：只检索当前用户的文档

```python
# 存储时添加 metadata
vector_store.add_documents(chunks, metadata={"user_id": user_id})

# 查询时过滤
results = vector_store.similarity_search(query, filter={"user_id": user_id})
```

## 项目结构

```
src/
├── api/v1/
│   ├── file.py          # 修改：上传成功后触发向量存储
│   ├── chat.py          # 新增：问答接口（后续）
├── services/
│   ├── embedding.py     # 新增：LLM 接入（DashScope Embedding）
│   ├── vector_store.py  # 新增：向量存储初始化
```

## 待实现

- [ ] 安装依赖：langchain, langchain-community, langchain-dashscope, pgvector, psycopg2-binary
- [ ] 创建 embedding 服务（DashScope text-embedding-v3）
- [ ] 创建向量存储服务（PGVector 初始化）
- [ ] 修改文件上传接口，后台触发向量存储
- [ ] 实现问答接口（chat.py）
