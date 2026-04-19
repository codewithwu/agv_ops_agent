"""VectorStoreService 集成测试.

测试 PDF、MD、TXT 三种文件类型的加载、分割、存储和检索流程。
需要真实的 PGVector 数据库和 Embedding 服务（Ollama）支持。
"""

from pathlib import Path

import pytest
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from src.services.vectorstore import VectorStoreService


class TestVectorStoreService:
    """VectorStoreService 集成测试."""

    @pytest.fixture
    def txt_file(self, tmp_path: Path) -> Path:
        """创建临时 txt 文件."""
        file_path = tmp_path / "test.txt"
        file_path.write_text(
            "AGV电池维护指南：\n"
            "1. 每日检查电池电量，电量低于20%时应及时充电。\n"
            "2. 充电时使用原装充电器，避免过充。\n"
            "3. 电池环境温度应保持在5-40摄氏度之间。\n"
            "4. 定期清洁电池仓，确保散热良好。",
            encoding="utf-8",
        )
        return file_path

    @pytest.fixture
    def md_file(self, tmp_path: Path) -> Path:
        """创建临时 md 文件."""
        file_path = tmp_path / "test.md"
        file_path.write_text(
            "# AGV 故障排查手册\n\n"
            "## 电池故障\n\n"
            "如果AGV无法启动，首先检查电池电量。如果电量充足但仍无法启动，可能是电池连接线松动。\n\n"
            "## 电机故障\n\n"
            "电机异常时检查驱动电机是否过热，过热会导致自动保护停机。\n\n"
            "## 传感器故障\n\n"
            "传感器失灵会导致AGV无法准确感知环境，需要定期校准。",
            encoding="utf-8",
        )
        return file_path

    @pytest.fixture
    def pdf_file(self, tmp_path: Path) -> Path:
        """创建临时 PDF 文件."""
        file_path = tmp_path / "test.pdf"
        c = canvas.Canvas(str(file_path), pagesize=A4)
        c.drawString(100, 800, "AGV Operation Manual")
        c.drawString(100, 780, "")
        c.drawString(100, 760, "Chapter 1: Daily Operation")
        c.drawString(100, 740, "1. Check battery level before startup")
        c.drawString(100, 720, "2. Verify sensors are functioning")
        c.drawString(100, 700, "3. Confirm route planning is correct")
        c.showPage()
        c.drawString(100, 800, "Chapter 2: Maintenance")
        c.drawString(100, 780, "1. Clean sensor lens weekly")
        c.drawString(100, 760, "2. Check tire wear monthly")
        c.drawString(100, 740, "3. Conduct full inspection quarterly")
        c.save()
        return file_path

    @pytest.fixture
    def txt_vectorstore(self) -> VectorStoreService:
        """TXT 测试用 VectorStoreService."""
        service = VectorStoreService(
            embedding_provider="ollama",
            collection_name="test_txt_docs",
            chunk_size=200,
            chunk_overlap=30,
        )
        yield service
        # 测试完成后清理 collection
        vs = service.get_vectorstore()
        vs.delete_collection()

    @pytest.fixture
    def md_vectorstore(self) -> VectorStoreService:
        """MD 测试用 VectorStoreService."""
        service = VectorStoreService(
            embedding_provider="ollama",
            collection_name="test_md_docs",
            chunk_size=200,
            chunk_overlap=30,
        )
        yield service
        vs = service.get_vectorstore()
        vs.delete_collection()

    @pytest.fixture
    def pdf_vectorstore(self) -> VectorStoreService:
        """PDF 测试用 VectorStoreService."""
        service = VectorStoreService(
            embedding_provider="ollama",
            collection_name="test_pdf_docs",
            chunk_size=200,
            chunk_overlap=30,
        )
        yield service
        vs = service.get_vectorstore()
        vs.delete_collection()

    def test_txt_process(
        self, txt_file: Path, txt_vectorstore: VectorStoreService
    ) -> None:
        """测试 TXT 文件的加载、分割、存储和检索."""
        # 1. 加载并存储
        doc_ids = txt_vectorstore.add_documents(
            txt_file,
            metadata={"file_type": "txt", "test": "true"},
        )
        assert len(doc_ids) > 0, "文档应被分割并存储"

        # 2. 检索
        vs = txt_vectorstore.get_vectorstore()
        results = vs.similarity_search("电池如何维护", k=2)

        assert len(results) > 0, "应能检索到相关内容"
        content = results[0].page_content
        assert "电池" in content, "检索结果应包含电池相关内容"

    def test_md_process(
        self, md_file: Path, md_vectorstore: VectorStoreService
    ) -> None:
        """测试 MD 文件的加载、分割、存储和检索."""
        # 1. 加载并存储
        doc_ids = md_vectorstore.add_documents(
            md_file,
            metadata={"file_type": "md", "test": "true"},
        )
        assert len(doc_ids) > 0, "文档应被分割并存储"

        # 2. 检索
        vs = md_vectorstore.get_vectorstore()
        results = vs.similarity_search("AGV无法启动怎么办", k=2)

        assert len(results) > 0, "应能检索到相关内容"
        content = results[0].page_content
        assert "AGV" in content or "电池" in content, "检索结果应包含AGV相关内容"

    def test_pdf_process(
        self, pdf_file: Path, pdf_vectorstore: VectorStoreService
    ) -> None:
        """测试 PDF 文件的加载、分割、存储和检索."""
        # 1. 加载并存储
        doc_ids = pdf_vectorstore.add_documents(
            pdf_file,
            metadata={"file_type": "pdf", "test": "true"},
        )
        assert len(doc_ids) > 0, "文档应被分割并存储"

        # 2. 检索
        vs = pdf_vectorstore.get_vectorstore()
        results = vs.similarity_search("AGV daily operation check", k=2)

        assert len(results) > 0, "应能检索到相关内容"
        content = results[0].page_content
        # 验证检索结果包含 PDF 中的相关内容
        assert "AGV" in content or "Operation" in content or "Chapter" in content, (
            f"检索结果应包含PDF相关内容，实际内容: {content}"
        )
