"""文档处理服务模块.

支持多种文档类型的加载与分割：
- PDF: PyPDFLoader + RecursiveCharacterTextSplitter
- MD: UnstructuredMarkdownLoader + MarkdownTextSplitter
- TXT: TextLoader + RecursiveCharacterTextSplitter
"""

from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar

from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
    UnstructuredMarkdownLoader,
)
from langchain_core.documents import Document
from langchain_text_splitters import (
    MarkdownTextSplitter,
    RecursiveCharacterTextSplitter,
)


@dataclass
class DocumentProcessResult:
    """文档处理结果."""

    documents: list[Document]
    file_path: str
    file_type: str
    chunk_count: int


class DocumentLoaderService:
    """文档加载服务."""

    _LOADER_MAP: ClassVar[dict[str, type] | dict[str, type]] = {
        ".pdf": PyPDFLoader,
        ".md": UnstructuredMarkdownLoader,
        ".txt": TextLoader,
    }

    def load(self, file_path: str | Path) -> list[Document]:
        """加载文档.

        Args:
            file_path: 文件路径

        Returns:
            文档列表

        Raises:
            FileNotFoundError: 文件不存在
            ValueError: 不支持的文件类型
        """
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")

        suffix = path.suffix.lower()
        if suffix not in self._LOADER_MAP:
            supported = ", ".join(self._LOADER_MAP.keys())
            raise ValueError(f"不支持的文件类型: {suffix}，支持: {supported}")

        loader_cls = self._LOADER_MAP[suffix]
        loader = loader_cls(str(path.resolve()))
        return loader.load()  # type: ignore[no-any-return]

    def load_with_metadata(
        self,
        file_path: str | Path,
        metadata: dict | None = None,
    ) -> list[Document]:
        """加载文档并附加元数据.

        Args:
            file_path: 文件路径
            metadata: 附加元数据

        Returns:
            文档列表
        """
        docs = self.load(file_path)
        if metadata is None:
            metadata = {}

        metadata.setdefault("source", str(file_path))
        for doc in docs:
            doc.metadata.update(metadata)

        return docs


class TextSplitterService:
    """文本分割服务."""

    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
    ) -> None:
        """初始化文本分割服务.

        Args:
            chunk_size: 每块最大字符数
            chunk_overlap: 相邻块重叠字符数
        """
        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap

    def _get_splitter(self, file_type: str):
        """根据文件类型获取分割器."""
        if file_type == ".md":
            return MarkdownTextSplitter(
                chunk_size=self._chunk_size,
                chunk_overlap=self._chunk_overlap,
                length_function=len,
                add_start_index=True,
            )
        return RecursiveCharacterTextSplitter(
            chunk_size=self._chunk_size,
            chunk_overlap=self._chunk_overlap,
            length_function=len,
            add_start_index=True,
        )

    def split(
        self,
        documents: list[Document],
        file_type: str,
    ) -> list[Document]:
        """分割文档列表.

        Args:
            documents: 文档列表
            file_type: 文件类型标识

        Returns:
            分割后的文档列表
        """
        splitter = self._get_splitter(file_type)
        return splitter.split_documents(documents)  # type: ignore[no-any-return]


class DocumentProcessorService:
    """文档处理服务（加载 + 分割一体化）."""

    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
    ) -> None:
        """初始化文档处理服务.

        Args:
            chunk_size: 每块最大字符数
            chunk_overlap: 相邻块重叠字符数
        """
        self._loader = DocumentLoaderService()
        self._splitter = TextSplitterService(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

    def process_file(
        self,
        file_path: str | Path,
        metadata: dict | None = None,
    ) -> DocumentProcessResult:
        """加载并分割文件（一次性完成）.

        Args:
            file_path: 文件路径
            metadata: 附加元数据

        Returns:
            DocumentProcessResult: 包含分割后的文档列表
        """
        path = Path(file_path)
        suffix = path.suffix.lower()

        docs = self._loader.load_with_metadata(path, metadata)
        split_docs = self._splitter.split(docs, suffix)

        return DocumentProcessResult(
            documents=split_docs,
            file_path=str(path.resolve()),
            file_type=suffix,
            chunk_count=len(split_docs),
        )
