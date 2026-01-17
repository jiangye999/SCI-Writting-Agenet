"""
Simple Document Parser - 支持PDF/Word/Excel/Markdown
Simple Document Parser - Support PDF/Word/Excel/Markdown
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class DocumentElement:
    """文档元素类"""

    element_type: str = "Text"
    text: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    page_number: Optional[int] = None


@dataclass
class ParsedSection:
    """解析的章节"""

    section_name: str = ""
    content: str = ""
    elements: List[DocumentElement] = field(default_factory=list)
    page_range: Tuple[int, int] = (0, 0)


class SimpleDocumentParser:
    """
    简单文档解析器
    支持: PDF, Word, Excel, Markdown, TXT
    """

    SECTION_PATTERNS = {
        "abstract": r"(?i)(?:^|\n)\s*(?:abstract|摘要)[\s:]*",
        "introduction": r"(?i)(?:^|\n)\s*(?:1\s*\.?|introduction|background)[\s:]*(.+?)",
        "methods": r"(?i)(?:^|\n)\s*(?:2\s*\.?|methods|materials and methods|methodology)[\s:]*(.+?)",
        "results": r"(?i)(?:^|\n)\s*(?:3\s*\.?|results|findings)[\s:]*(.+?)",
        "discussion": r"(?i)(?:^|\n)\s*(?:4\s*\.?|discussion)[\s:]*(.+?)",
        "conclusion": r"(?i)(?:^|\n)\s*(?:5\s*\.?|conclusion|conclusions)[\s:]*(.+?)",
        "references": r"(?i)(?:^|\n)\s*(?:references|bibliography)[\s:]*",
    }

    def __init__(self):
        pass

    def parse(self, file_path: str) -> List[DocumentElement]:
        """
        解析文档

        Args:
            file_path: 文件路径

        Returns:
            元素列表
        """
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")

        suffix = path.suffix.lower()

        if suffix in [".txt", ".md"]:
            return self._parse_text(path)
        elif suffix == ".pdf":
            return self._parse_pdf(path)
        elif suffix in [".docx", ".doc"]:
            return self._parse_word(path)
        elif suffix in [".xlsx", ".xls", ".csv"]:
            return self._parse_excel(path)
        else:
            raise ValueError(f"不支持的格式: {suffix}")

    def _parse_text(self, path: Path) -> List[DocumentElement]:
        """解析文本/Markdown文件"""
        text = path.read_text(encoding="utf-8")

        # 按段落分割
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

        elements = []
        for i, para in enumerate(paragraphs):
            if re.match(r"^(#+|[0-9]+\.|[A-Z][a-z]+:)", para.strip()):
                elem_type = "Title"
            elif para.startswith("#"):
                elem_type = "Title"
            else:
                elem_type = "Paragraph"

            elements.append(
                DocumentElement(
                    element_type=elem_type, text=para, metadata={"paragraph": i}
                )
            )

        return elements

    def _parse_pdf(self, path: Path) -> List[DocumentElement]:
        """解析PDF文件 - 使用Docling智能解析"""
        try:
            from docling.document_converter import DocumentConverter

            converter = DocumentConverter()
            result = converter.convert(str(path))

            if result.document:
                # 使用Markdown导出，保持文档结构
                markdown_text = result.document.export_to_markdown()

                if markdown_text:
                    elements = []

                    # 按行处理Markdown文本
                    lines = markdown_text.split("\n")
                    for line in lines:
                        line = line.strip()
                        if line:
                            # 判断是否为标题（Markdown格式）
                            if line.startswith("#"):
                                elem_type = "Title"
                            elif re.match(
                                r"^(?:\d+\.?\s*)?[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*$", line
                            ):
                                elem_type = "Title"
                            else:
                                elem_type = "Paragraph"

                            elements.append(
                                DocumentElement(
                                    element_type=elem_type,
                                    text=line[:5000] if len(line) > 5000 else line,
                                    metadata={"page": 0},
                                )
                            )

                    if elements:
                        return elements

            # 如果Docling解析失败，回退到原始方法
            raise ValueError("Docling returned empty document")

        except ImportError:
            raise ImportError("请安装docling: pip install docling")
        except Exception as e:
            print(f"Docling解析失败，回退到原始方法: {e}")
            return self._parse_pdf_fallback(path)

    def _parse_pdf_fallback(self, path: Path) -> List[DocumentElement]:
        """回退的PDF解析方法 - 使用pdfplumber"""
        try:
            import pdfplumber

            with pdfplumber.open(str(path)) as pdf:
                elements = []
                page_num = 0

                for page in pdf.pages:
                    page_num += 1
                    text = page.extract_text() or ""

                    if not text.strip():
                        continue

                    lines = text.split("\n")
                    for line in lines:
                        line = line.strip()
                        if line:
                            if re.match(
                                r"^(?:\d+\.?\s*)?[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*$", line
                            ):
                                elem_type = "Title"
                            else:
                                elem_type = "Paragraph"

                            elements.append(
                                DocumentElement(
                                    element_type=elem_type,
                                    text=line,
                                    metadata={"page": page_num},
                                )
                            )

                return elements

        except ImportError:
            raise ImportError("请安装pdfplumber: pip install pdfplumber")

    def _parse_word(self, path: Path) -> List[DocumentElement]:
        """解析Word文档"""
        try:
            from docx import Document

            doc = Document(str(path))
            elements = []
            para_num = 0

            for para in doc.paragraphs:
                text = para.text.strip()
                if text:
                    para_num += 1

                    # 检测标题
                    if para.style.name.startswith("Heading"):
                        elem_type = "Title"
                    elif re.match(
                        r"^(?:\d+\.?\s*)?[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*$", text
                    ):
                        elem_type = "Title"
                    else:
                        elem_type = "Paragraph"

                    elements.append(
                        DocumentElement(
                            element_type=elem_type,
                            text=text,
                            metadata={"paragraph": para_num},
                        )
                    )

            return elements

        except ImportError:
            raise ImportError("请安装python-docx: pip install python-docx")

    def _parse_excel(self, path: Path) -> List[DocumentElement]:
        """解析Excel文件 - 精准识别每个单元格"""
        try:
            import pandas as pd

            # 读取所有sheet
            if path.suffix == ".csv":
                df = pd.read_csv(str(path))
            else:
                df = pd.read_excel(str(path))

            elements = []
            element_id = 0

            # 1. 添加表格基本信息
            elements.append(
                DocumentElement(
                    element_type="TableInfo",
                    text=f"表格名称: {path.stem}",
                    metadata={"element_id": element_id},
                )
            )
            element_id += 1

            # 2. 添加列名信息
            columns = df.columns.tolist()
            elements.append(
                DocumentElement(
                    element_type="Columns",
                    text=f"列名: {', '.join(columns)}",
                    metadata={"columns": columns, "element_id": element_id},
                )
            )
            element_id += 1

            # 3. 逐行解析每一行数据（精准到每个单元格）
            for row_idx, row in df.iterrows():
                row_data = []
                for col_idx, (col_name, value) in enumerate(row.items()):
                    # 格式化每个单元格的值
                    cell_value = str(value) if pd.notna(value) else ""
                    if cell_value and cell_value != "nan":
                        row_data.append(f"{col_name}: {cell_value}")

                if row_data:
                    elements.append(
                        DocumentElement(
                            element_type="Row",
                            text=" | ".join(row_data),
                            metadata={
                                "row_index": row_idx,
                                "columns": columns,
                                "element_id": element_id,
                            },
                        )
                    )
                    element_id += 1

            # 4. 添加统计信息
            elements.append(
                DocumentElement(
                    element_type="TableStats",
                    text=f"总行数: {len(df)}, 总列数: {len(columns)}",
                    metadata={
                        "total_rows": len(df),
                        "total_columns": len(columns),
                        "element_id": element_id,
                    },
                )
            )

            return elements

        except ImportError:
            raise ImportError("请安装openpyxl和pandas: pip install openpyxl pandas")

    def extract_sections(self, file_path: str) -> Dict[str, ParsedSection]:
        """从文档中提取章节"""
        elements = self.parse(file_path)
        full_text = "\n".join([elem.text for elem in elements])

        sections = {}
        sorted_sections = []

        for section_name, pattern in self.SECTION_PATTERNS.items():
            match = re.search(pattern, full_text, re.DOTALL | re.IGNORECASE)
            if match:
                sorted_sections.append((section_name, match.start()))

        sorted_sections.sort(key=lambda x: x[1])

        for i, (section_name, start_pos) in enumerate(sorted_sections):
            end_pos = (
                sorted_sections[i + 1][1]
                if i < len(sorted_sections) - 1
                else len(full_text)
            )
            content = full_text[start_pos:end_pos].strip()

            if content:
                sections[section_name] = ParsedSection(
                    section_name=section_name,
                    content=content,
                )

        return sections

    def extract_full_text(self, file_path: str) -> str:
        """提取完整文本"""
        elements = self.parse(file_path)
        return "\n\n".join([elem.text for elem in elements])

    def extract_table_data(self, file_path: str) -> Dict[str, Any]:
        """专门用于提取表格数据，返回结构化格式"""
        if not Path(file_path).suffix.lower() in [".xlsx", ".xls", ".csv"]:
            raise ValueError("只有Excel/CSV文件支持表格数据提取")

        import pandas as pd

        if file_path.endswith(".csv"):
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path)

        return {
            "columns": df.columns.tolist(),
            "data": df.to_dict(orient="records"),
            "shape": {"rows": len(df), "columns": len(df.columns)},
            "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
        }


class DocumentProcessor:
    """统一文档处理器"""

    def __init__(self, use_api: bool = False):
        self.processor = SimpleDocumentParser()

    def parse(self, file_path: str) -> List[DocumentElement]:
        return self.processor.parse(file_path)

    def extract_sections(self, file_path: str) -> Dict[str, ParsedSection]:
        return self.processor.extract_sections(file_path)

    def extract_full_text(self, file_path: str) -> str:
        return self.processor.extract_full_text(file_path)

    def extract_table_data(self, file_path: str) -> Dict[str, Any]:
        return self.processor.extract_table_data(file_path)


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("用法: python simple_parser.py <文件路径>")
        sys.exit(1)

    parser = SimpleDocumentParser()
    file_path = sys.argv[1]

    print(f"解析文件: {file_path}")
    elements = parser.parse(file_path)
    print(f"提取了 {len(elements)} 个元素")

    # 如果是表格，显示结构化数据
    if file_path.endswith((".xlsx", ".xls", ".csv")):
        print("\n表格数据:")
        table_data = parser.extract_table_data(file_path)
        print(f"列名: {table_data['columns']}")
        print(f"行数: {table_data['shape']['rows']}")
        print("\n前3行数据:")
        for row in table_data["data"][:3]:
            print(row)
