"""向量存储服务模块.

基于 PostgreSQL 的向量存储（PGVector），支持：
- 文档向量化存储与相似度检索
- 与已有 Embedding 服务集成
"""

from functools import lru_cache
from pathlib import Path
from typing import Annotated

from langchain_postgres.vectorstores import PGVector

from src.config import settings
from src.services.document_processor import DocumentProcessorService
from src.services.embedding import get_embedding_service


class VectorStoreService:
    """PGVector 向量存储服务."""

    def __init__(
        self,
        embedding_provider: str = "ollama",
        collection_name: str = "agv_docs",
        chunk_size: int = 500,
        chunk_overlap: int = 50,
    ) -> None:
        """初始化向量存储服务.

        Args:
            embedding_provider: Embedding 提供者 ("ollama" 或 "openai")
            collection_name: 向量集合名称
            chunk_size: 文档分割块大小
            chunk_overlap: 文档分割块重叠大小
        """
        self._embedding_service = get_embedding_service(embedding_provider)
        self._embeddings = self._embedding_service.as_langchain()
        self._collection_name = collection_name
        self._connection = settings.pgvector_connection
        self._vectorstore: PGVector | None = None
        self._doc_processor = DocumentProcessorService(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

    def _get_vectorstore(self) -> PGVector:
        """获取或创建 PGVector 实例（懒加载）."""
        if self._vectorstore is None:
            self._vectorstore = PGVector(
                self._embeddings,
                connection=self._connection,
                collection_name=self._collection_name,
                pre_delete_collection=False,
            )
        return self._vectorstore

    def get_vectorstore(self) -> PGVector:
        """获取 PGVector 实例."""
        return self._get_vectorstore()

    def add_documents(
        self,
        file_path: str | Path,
        metadata: dict | None = None,
    ) -> list[str]:
        """加载并分割文档，然后添加到向量存储.

        Args:
            file_path: 文件路径
            metadata: 附加元数据

        Returns:
            文档 ID 列表
        """
        result = self._doc_processor.process_file(file_path, metadata)
        return self._get_vectorstore().add_documents(result.documents)  # type: ignore[no-any-return]


@lru_cache()
def get_vectorstore_service(
    embedding_provider: Annotated[
        str, "Embedding provider: 'ollama' or 'openai'"
    ] = "ollama",
    collection_name: Annotated[
        str, "Collection name for the vector store"
    ] = "agv_docs",
    chunk_size: Annotated[int, "Document chunk size"] = 500,
    chunk_overlap: Annotated[int, "Document chunk overlap"] = 50,
) -> VectorStoreService:
    """获取向量存储服务实例（单例）.

    Args:
        embedding_provider: Embedding 提供者
        collection_name: 向量集合名称
        chunk_size: 文档分割块大小
        chunk_overlap: 文档分割块重叠大小

    Returns:
        VectorStoreService 实例
    """
    return VectorStoreService(
        embedding_provider=embedding_provider,
        collection_name=collection_name,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
