"""DocumentProcessor 服务测试."""

from pathlib import Path

import pytest
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from src.services.document_processor import (
    DocumentLoaderService,
    DocumentProcessorService,
    DocumentProcessResult,
)


class TestDocumentLoaderService:
    """DocumentLoaderService 测试."""

    @pytest.fixture
    def loader(self) -> DocumentLoaderService:
        """DocumentLoaderService 实例."""
        return DocumentLoaderService()

    @pytest.fixture
    def txt_file(self, tmp_path: Path) -> Path:
        """创建临时 txt 文件."""
        file_path = tmp_path / "test.txt"
        file_path.write_text("这是测试文本内容。\n第二行内容。", encoding="utf-8")
        return file_path

    @pytest.fixture
    def md_file(self, tmp_path: Path) -> Path:
        """创建临时 md 文件."""
        file_path = tmp_path / "test.md"
        file_path.write_text(
            "# 测试标题\n\n这是测试内容。\n\n## 子标题\n\n更多内容。",
            encoding="utf-8",
        )
        return file_path

    @pytest.fixture
    def pdf_file(self, tmp_path: Path) -> Path:
        """创建临时 PDF 文件."""
        file_path = tmp_path / "test.pdf"
        c = canvas.Canvas(str(file_path), pagesize=A4)
        c.drawString(100, 800, "这是 PDF 第一页内容。")
        c.showPage()
        c.drawString(100, 800, "这是 PDF 第二页内容。")
        c.save()
        return file_path

    def test_load_txt(self, loader: DocumentLoaderService, txt_file: Path) -> None:
        """测试加载 TXT 文件."""
        docs = loader.load(txt_file)

        assert len(docs) == 1
        assert "这是测试文本内容" in docs[0].page_content

    def test_load_md(self, loader: DocumentLoaderService, md_file: Path) -> None:
        """测试加载 MD 文件."""
        docs = loader.load(md_file)

        assert len(docs) >= 1
        content = docs[0].page_content
        assert "测试标题" in content or "测试内容" in content

    def test_load_pdf(self, loader: DocumentLoaderService, pdf_file: Path) -> None:
        """测试加载 PDF 文件."""
        docs = loader.load(pdf_file)

        assert len(docs) == 2  # PDF 有两页
        content = " ".join(doc.page_content for doc in docs)
        assert "PDF" in content

    def test_load_with_metadata(
        self, loader: DocumentLoaderService, txt_file: Path
    ) -> None:
        """测试加载文件并附加元数据."""
        custom_metadata = {"author": "tester", "version": "1.0"}
        docs = loader.load_with_metadata(txt_file, metadata=custom_metadata)

        assert len(docs) == 1
        assert docs[0].metadata["author"] == "tester"
        assert docs[0].metadata["version"] == "1.0"
        assert docs[0].metadata["source"] == str(txt_file)

    def test_load_file_not_found(self, loader: DocumentLoaderService) -> None:
        """测试文件不存在的情况."""
        with pytest.raises(FileNotFoundError):
            loader.load("/nonexistent/file.txt")

    def test_load_unsupported_file_type(
        self, loader: DocumentLoaderService, tmp_path: Path
    ) -> None:
        """测试不支持的文件类型."""
        unsupported_file = tmp_path / "test.docx"
        unsupported_file.write_text("test content")

        with pytest.raises(ValueError, match="不支持的文件类型"):
            loader.load(unsupported_file)


class TestDocumentProcessorService:
    """DocumentProcessorService 测试（加载 + 分割一体化）."""

    @pytest.fixture
    def processor(self) -> DocumentProcessorService:
        """DocumentProcessorService 实例."""
        return DocumentProcessorService(chunk_size=200, chunk_overlap=20)

    @pytest.fixture
    def txt_file(self, tmp_path: Path) -> Path:
        """创建临时 txt 文件."""
        file_path = tmp_path / "test.txt"
        # 内容超过 200 字符，确保会被分割
        file_path.write_text(
            "这是第一段测试内容。" * 20,
            encoding="utf-8",
        )
        return file_path

    @pytest.fixture
    def md_file(self, tmp_path: Path) -> Path:
        """创建临时 md 文件."""
        file_path = tmp_path / "test.md"
        file_path.write_text(
            "# 主标题\n\n这是第一段内容。\n\n## 子标题\n\n这是第二段内容。",
            encoding="utf-8",
        )
        return file_path

    @pytest.fixture
    def pdf_file(self, tmp_path: Path) -> Path:
        """创建临时 PDF 文件."""
        file_path = tmp_path / "test.pdf"
        c = canvas.Canvas(str(file_path), pagesize=A4)
        c.drawString(100, 800, "这是 PDF 第一页内容。")
        c.showPage()
        c.drawString(100, 800, "这是 PDF 第二页内容。")
        c.save()
        return file_path

    def test_process_file_txt(
        self, processor: DocumentProcessorService, txt_file: Path
    ) -> None:
        """测试处理 TXT 文件（加载 + 分割）."""
        result = processor.process_file(txt_file)

        assert isinstance(result, DocumentProcessResult)
        assert result.file_type == ".txt"
        assert result.file_path == str(txt_file.resolve())
        assert result.chunk_count >= 1
        assert len(result.documents) == result.chunk_count

    def test_process_file_md(
        self, processor: DocumentProcessorService, md_file: Path
    ) -> None:
        """测试处理 MD 文件（加载 + 分割）."""
        result = processor.process_file(md_file)

        assert isinstance(result, DocumentProcessResult)
        assert result.file_type == ".md"
        assert result.chunk_count >= 1

    def test_process_file_pdf(
        self, processor: DocumentProcessorService, pdf_file: Path
    ) -> None:
        """测试处理 PDF 文件（加载 + 分割）."""
        result = processor.process_file(pdf_file)

        assert isinstance(result, DocumentProcessResult)
        assert result.file_type == ".pdf"
        assert result.chunk_count >= 1

    def test_process_file_with_metadata(
        self, processor: DocumentProcessorService, txt_file: Path
    ) -> None:
        """测试处理文件并附加元数据."""
        metadata = {"author": "tester", "department": "ops"}
        result = processor.process_file(txt_file, metadata=metadata)

        assert result.chunk_count >= 1
        for doc in result.documents:
            assert doc.metadata["author"] == "tester"
            assert doc.metadata["department"] == "ops"
