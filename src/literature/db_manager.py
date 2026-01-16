"""
文献数据库管理器模块
"""

import json
import re
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd


@dataclass
class Paper:
    """论文数据类"""

    id: Optional[int] = None
    wos_id: str = ""
    title: str = ""
    authors: str = ""
    journal: str = ""
    year: int = 0
    volume: str = ""
    issue: str = ""
    pages: str = ""
    doi: str = ""
    abstract: str = ""
    keywords: str = ""
    cited_by: int = 0
    research_area: str = ""
    # citekey字段：格式为 Author2025 (如: Zhang2025)
    citekey: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "wos_id": self.wos_id,
            "title": self.title,
            "authors": self.authors,
            "journal": self.journal,
            "year": self.year,
            "volume": self.volume,
            "issue": self.issue,
            "pages": self.pages,
            "doi": self.doi,
            "abstract": self.abstract,
            "keywords": self.keywords,
            "cited_by": self.cited_by,
            "research_area": self.research_area,
            "citekey": self.citekey,
        }

    def generate_citekey(self) -> str:
        """
        生成标准citekey格式: AuthorYYYY
        例如: Zhang2025, Smith2023
        如果作者名超过15字符，使用前15字符
        """
        # 提取第一作者姓氏
        first_author_lastname = ""
        if self.authors:
            # 尝试多种格式
            if ";" in self.authors:
                first_author = self.authors.split(";")[0].strip()
            elif "," in self.authors:
                first_author = self.authors.split(",")[0].strip()
            elif " and " in self.authors:
                first_author = self.authors.split(" and ")[0].strip()
            else:
                first_author = self.authors.strip()

            # 提取姓氏（假设格式为 "Smith, John" 或 "John Smith"）
            if "," in first_author:
                parts = first_author.split(",")
                if len(parts) >= 1:
                    first_author_lastname = parts[0].strip()
                if len(parts) >= 2:
                    # 可能是 "Smith, John" 格式
                    first_author_lastname = parts[0].strip()
            else:
                # 可能是 "John Smith" 格式，取最后一个词
                parts = first_author.split()
                if parts:
                    first_author_lastname = parts[-1]

        # 清理姓氏，只保留字母
        first_author_lastname = re.sub(r"[^a-zA-Z]", "", first_author_lastname)

        # 限制长度
        first_author_lastname = first_author_lastname[:15]

        # 如果无法提取作者，使用 "Unknown"
        if not first_author_lastname:
            first_author_lastname = "Unknown"

        # 首字母大写
        first_author_lastname = first_author_lastname.capitalize()

        # 组合为 citekey
        if self.year > 0:
            return f"{first_author_lastname}{self.year}"
        else:
            return f"{first_author_lastname}"

    def format_citation(
        self, citation_style: str = "author-year", citekey: str = ""
    ) -> str:
        """
        根据引用风格生成文中引用格式

        Args:
            citation_style: 引用风格 ("author-year" 或 "numbered")
            citekey: 自定义citekey，如果为空则使用generate_citekey()

        Returns:
            文中引用格式字符串
        """
        key = citekey or self.generate_citekey()

        if citation_style == "numbered":
            # 编号格式需要从数据库获取序号，这里返回占位符
            return f"\\citep{{{key}}}"
        else:
            # 作者-年份格式
            first_author = "Unknown"
            if self.authors:
                parts = self.authors.split(",")[0].split(";")[0].strip().split()
                if parts:
                    first_author = parts[-1]

            if self.year > 0:
                return f"\\citep{{{key}}}"
            else:
                return f"\\citep{{{key}}}"

    def to_bibtex(self, reference_format: str = "nature") -> str:
        """
        生成BibTeX格式条目

        Args:
            reference_format: 参考文献格式 ("nature", "apa", "vancouver", "ieee")

        Returns:
            BibTeX条目字符串
        """
        # 生成citekey
        citekey = self.generate_citekey()

        # 清理标题中的花括号和特殊字符
        title = self.title.replace("{", "").replace("}", "").replace("\n", " ")

        # 清理作者格式
        authors = self.authors.replace(";", " and ")

        # 根据引用风格生成不同的BibTeX格式
        if reference_format == "apa":
            # APA风格: Author (Year). Title. Journal, Volume(Issue), Pages.
            entry = f"""@article{{{citekey},
  author = {{{authors}}},
  title = {{{title}}},
  journal = {{{self.journal}}},
  year = {{{self.year}}},
  volume = {{{self.volume}}},
  number = {{{self.issue}}},
  pages = {{{self.pages}}},
  doi = {{{self.doi}}}
}}"""
        elif reference_format == "vancouver":
            # Vancouver风格: Author. Title. Journal. Year;Volume:Pages.
            entry = f"""@article{{{citekey},
  author = {{{authors}}},
  title = {{{title}}},
  journal = {{{self.journal}}},
  year = {{{self.year}}},
  volume = {{{self.volume}}},
  pages = {{{self.pages}}}
}}"""
        elif reference_format == "ieee":
            # IEEE风格
            entry = f"""@article{{{citekey},
  author = {{{authors}}},
  title = {{{title}}},
  journal = {{{self.journal}}},
  year = {{{self.year}}},
  volume = {{{self.volume}}},
  number = {{{self.issue}}},
  pages = {{{self.pages}}},
  doi = {{{self.doi}}}
}}"""
        else:
            # Nature风格 (默认)
            entry = f"""@article{{{citekey},
  author = {{{authors}}},
  title = {{{title}}},
  journal = {{{self.journal}}},
  year = {{{self.year}}},
  volume = {{{self.volume}}},
  number = {{{self.issue}}},
  pages = {{{self.pages}}},
  doi = {{{self.doi}}},
  abstract = {{{self.abstract}}},
}}"""

        return entry

    def get_full_reference_info(
        self, reference_format: str = "nature"
    ) -> Dict[str, str]:
        """
        获取完整引用信息：citekey, bibtex, abstract

        Args:
            reference_format: 参考文献格式

        Returns:
            包含 citekey, bibtex, abstract 的字典
        """
        return {
            "citekey": self.generate_citekey(),
            "bibtex": self.to_bibtex(reference_format),
            "abstract": self.abstract,
            "authors": self.authors,
            "year": str(self.year),
            "title": self.title,
            "journal": self.journal,
        }


@dataclass
class Citation:
    """引用数据类"""

    id: Optional[int] = None
    paper_id: int = 0
    in_text_format: str = ""  # 如 "(Zhang et al., 2022)"
    reference_format: str = ""  # 完整的参考文献格式


class LiteratureDatabaseManager:
    """文献数据库管理器"""

    def __init__(self, db_path: str = "data/literature.db"):
        """
        初始化管理器

        Args:
            db_path: 数据库文件路径
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()

    def _init_database(self) -> None:
        """初始化数据库表结构"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        # 论文表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS papers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                wos_id TEXT UNIQUE,
                title TEXT NOT NULL,
                authors TEXT,
                journal TEXT,
                year INTEGER,
                volume TEXT,
                issue TEXT,
                pages TEXT,
                doi TEXT UNIQUE,
                abstract TEXT,
                keywords TEXT,
                cited_by INTEGER,
                research_area TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 引用表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS citations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                paper_id INTEGER,
                in_text_format TEXT,
                reference_format TEXT,
                FOREIGN KEY (paper_id) REFERENCES papers(id)
            )
        """)

        # 索引
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_year ON papers(year)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_journal ON papers(journal)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_doi ON papers(doi)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_keywords ON papers(keywords)")

        conn.commit()
        conn.close()

    def import_from_wos_excel(self, excel_path: str) -> int:
        """
        从Web of Science导出的Excel文件导入

        Args:
            excel_path: Excel文件路径

        Returns:
            导入的论文数量
        """
        df = pd.read_excel(excel_path)

        # 标准化列名
        column_mapping = {
            "Authors": "authors",
            "Author": "authors",
            "Title": "title",
            "Journal": "journal",
            "Book Title": "journal",
            "Year": "year",
            "Publication Year": "year",
            "Volume": "volume",
            "Issue": "issue",
            "Pages": "pages",
            "Page Range": "pages",
            "DOI": "doi",
            "Digital Object Identifier": "doi",
            "Abstract": "abstract",
            "Keywords": "keywords",
            "Author Keywords": "keywords",
            "Cited By": "cited_by",
            "Times Cited": "cited_by",
            "Research Area": "research_area",
            "Web of Science ID": "wos_id",
            "UT": "wos_id",
        }

        df = df.rename(columns=column_mapping)

        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        count = 0
        for _, row in df.iterrows():
            try:
                # 确保年份是整数
                year = int(row.get("year", 0)) if pd.notna(row.get("year")) else 0

                cursor.execute(
                    """
                    INSERT OR REPLACE INTO papers 
                    (wos_id, title, authors, journal, year, volume, issue, pages, 
                     doi, abstract, keywords, cited_by, research_area)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        str(row.get("wos_id", ""))[:100],
                        str(row.get("title", ""))[:500],
                        str(row.get("authors", ""))[:1000],
                        str(row.get("journal", ""))[:200],
                        year,
                        str(row.get("volume", ""))[:50],
                        str(row.get("issue", ""))[:50],
                        str(row.get("pages", ""))[:50],
                        str(row.get("doi", ""))[:100],
                        str(row.get("abstract", ""))[:5000]
                        if pd.notna(row.get("abstract"))
                        else "",
                        str(row.get("keywords", ""))[:500]
                        if pd.notna(row.get("keywords"))
                        else "",
                        int(row.get("cited_by", 0))
                        if pd.notna(row.get("cited_by"))
                        else 0,
                        str(row.get("research_area", ""))[:100],
                    ),
                )
                count += 1
            except Exception as e:
                print(f"导入论文失败: {row.get('title', 'Unknown')[:50]}... - {e}")
                continue

        conn.commit()
        conn.close()

        return count

    def import_from_wos_txt(self, txt_path: str) -> int:
        """
        从Web of Science导出的Plain Text .txt文件导入

        WOS TXT格式说明：
        - 每条记录以 ER 结束
        - 字段格式：PT xxx, AU xxx, TI xxx, AB xxx 等
        - 摘要AB和作者AU可能跨行

        Args:
            txt_path: TXT文件路径

        Returns:
            导入的论文数量
        """
        import json
        import hashlib

        # 读取文件内容
        with open(txt_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()

        # 按 ER 切分记录
        records = content.split("\nER\n")

        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        count = 0

        for record in records:
            if not record.strip():
                continue

            try:
                # 解析各字段
                paper_id = self._extract_field(record, "UT")
                doi = self._extract_field(record, "DI")
                title = self._extract_field(record, "TI")
                abstract = self._extract_field(record, "AB")
                year_str = self._extract_field(record, "PY")

                # 提取作者
                authors_raw = self._extract_all_fields(record, "AU")
                authors_full = self._extract_all_fields(record, "AF")

                # 解析作者列表
                if authors_full:
                    authors = "; ".join(authors_full)
                elif authors_raw:
                    authors = "; ".join(authors_raw)
                else:
                    authors = ""

                # 解析第一作者姓氏（用于引用）
                first_author = ""
                if authors_raw:
                    first_author = authors_raw[0].split(",")[0].strip()
                elif authors:
                    first_author = authors.split(",")[0].strip().split()[-1]

                # 年份处理
                year = 0
                if year_str:
                    try:
                        year = int(year_str[:4])
                    except (ValueError, TypeError):
                        year = 0

                # 生成paper_id
                if paper_id:
                    paper_id_value = f"wos:{paper_id}"
                elif doi:
                    paper_id_value = f"doi:{doi}"
                else:
                    # 使用title+year生成稳定ID
                    title_hash = hashlib.md5(f"{title}{year}".encode()).hexdigest()[:16]
                    paper_id_value = f"hash:{title_hash}"

                # 清洗摘要
                abstract_cleaned = self._clean_abstract(abstract)

                # 生成引用文本
                if first_author and year > 0:
                    citation_text = f"({first_author} et al., {year})"
                elif authors and year > 0:
                    citation_text = f"({authors.split(',')[0].strip()}, {year})"
                else:
                    citation_text = ""

                # 提取其他字段
                journal = self._extract_field(record, "SO")  # 期刊名是SO字段
                volume = self._extract_field(record, "VL")
                issue = self._extract_field(record, "IS")
                pages = self._extract_field(record, "BP", "")
                end_page = self._extract_field(record, "EP", "")
                if pages and end_page:
                    pages = f"{pages}-{end_page}"
                keywords = self._extract_field(record, "DE", "")
                research_area = self._extract_field(record, "SC", "")
                cited_by_str = self._extract_field(record, "TC", "0")
                try:
                    cited_by = int(cited_by_str) if cited_by_str else 0
                except ValueError:
                    cited_by = 0

                # 插入数据库
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO papers 
                    (wos_id, title, authors, journal, year, volume, issue, pages, 
                     doi, abstract, keywords, cited_by, research_area)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        paper_id_value[:100],
                        title[:500] if title else "",
                        authors[:1000] if authors else "",
                        journal[:200] if journal else "",
                        year,
                        volume[:50] if volume else "",
                        issue[:50] if issue else "",
                        pages[:50] if pages else "",
                        doi[:100] if doi else "",
                        abstract_cleaned[:5000] if abstract_cleaned else "",
                        keywords[:500] if keywords else "",
                        cited_by,
                        research_area[:100] if research_area else "",
                    ),
                )
                count += 1

            except Exception as e:
                print(f"导入论文失败: {str(e)[:100]}")
                continue

        conn.commit()
        conn.close()

        return count

    def _extract_field(self, record: str, field: str, default: str = "") -> str:
        """
        从记录中提取单个字段值

        WOS格式字段可能在行首或跨行，需要特殊处理
        """
        # WOS TXT格式：字段名后可能有多个空格，然后是内容
        # 例如：PT xxx 或 AU xxx, xxx
        pattern = rf"\n{field}\s+(.+?)(?=\n[A-Z]{{2}}\s+|\Z)"
        match = re.search(pattern, record, re.DOTALL)

        if match:
            value = match.group(1).strip()
            # 清理多余空白，保留科学符号
            value = re.sub(r"\s+", " ", value)
            return value

        # 尝试匹配行首的字段
        if record.startswith(f"{field} "):
            lines = record.split("\n")
            first_line = lines[0][len(field) + 1 :].strip()
            return re.sub(r"\s+", " ", first_line)

        return default

    def _extract_all_fields(self, record: str, field: str) -> List[str]:
        """
        从记录中提取所有匹配的字段值（用于AU等可能有多个的字段）
        """
        values = []
        pattern = rf"\n{field}\s+(.+?)(?=\n[A-Z]{{2}}\s+|\Z)"
        matches = re.findall(pattern, record, re.DOTALL)

        for match in matches:
            value = match.strip()
            # 清理但保留格式
            values.append(value)

        # 也检查行首
        lines = record.split("\n")
        for line in lines:
            if line.startswith(f"{field} "):
                value = line[len(field) + 1 :].strip()
                if value and value not in values:
                    values.append(value)

        return values

    def _clean_abstract(self, abstract: str) -> str:
        """
        清洗摘要，合并换行保留科学符号
        """
        if not abstract:
            return ""

        # 合并换行为空格
        cleaned = abstract.replace("\n", " ")

        # 多个空格合并为单个
        cleaned = re.sub(r" +", " ", cleaned)

        # 清理首尾空白
        cleaned = cleaned.strip()

        return cleaned

    def search(
        self,
        query: str,
        limit: int = 20,
        year_min: Optional[int] = None,
        year_max: Optional[int] = None,
        journal: Optional[str] = None,
        cited_by_min: int = 0,
        order_by: str = "year",
    ) -> List[Paper]:
        """
        搜索论文

        Args:
            query: 搜索关键词
            limit: 返回数量限制
            year_min: 最早年份
            year_max: 最晚年份
            journal: 期刊名称过滤
            cited_by_min: 最少引用数
            order_by: 排序字段 (year, cited_by, title)

        Returns:
            匹配的论文列表
        """
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        sql = """
            SELECT id, wos_id, title, authors, journal, year, volume, issue, 
                   pages, doi, abstract, keywords, cited_by, research_area
            FROM papers 
            WHERE (title LIKE ? OR abstract LIKE ? OR keywords LIKE ?)
        """
        params = [f"%{query}%", f"%{query}%", f"%{query}%"]

        if year_min:
            sql += " AND year >= ?"
            params.append(year_min)
        if year_max:
            sql += " AND year <= ?"
            params.append(year_max)
        if journal:
            sql += " AND journal LIKE ?"
            params.append(f"%{journal}%")
        if cited_by_min > 0:
            sql += " AND cited_by >= ?"
            params.append(cited_by_min)

        # 排序
        if order_by == "cited_by":
            sql += " ORDER BY cited_by DESC"
        elif order_by == "title":
            sql += " ORDER BY title"
        else:
            sql += " ORDER BY year DESC"

        sql += f" LIMIT {limit}"

        cursor.execute(sql, params)
        rows = cursor.fetchall()
        conn.close()

        return [self._row_to_paper(row) for row in rows]

    def _row_to_paper(self, row: Tuple) -> Paper:
        """将数据库行转换为Paper对象"""
        return Paper(
            id=row[0],
            wos_id=row[1],
            title=row[2],
            authors=row[3],
            journal=row[4],
            year=row[5],
            volume=row[6],
            issue=row[7],
            pages=row[8],
            doi=row[9],
            abstract=row[10],
            keywords=row[11],
            cited_by=row[12],
            research_area=row[13],
        )

    def get_paper_by_id(self, paper_id: int) -> Optional[Paper]:
        """根据ID获取论文"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, wos_id, title, authors, journal, year, volume, issue, 
                   pages, doi, abstract, keywords, cited_by, research_area
            FROM papers WHERE id = ?
        """,
            (paper_id,),
        )
        row = cursor.fetchone()
        conn.close()

        return self._row_to_paper(row) if row else None

    def get_paper_by_doi(self, doi: str) -> Optional[Paper]:
        """根据DOI获取论文"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, wos_id, title, authors, journal, year, volume, issue, 
                   pages, doi, abstract, keywords, cited_by, research_area
            FROM papers WHERE doi = ?
        """,
            (doi,),
        )
        row = cursor.fetchone()
        conn.close()

        return self._row_to_paper(row) if row else None

    def format_citation(self, paper: Paper, style: str = "author-year") -> str:
        """
        生成引用格式

        Args:
            paper: 论文对象
            style: 格式风格 ('author-year' 或 'numbered')

        Returns:
            引用字符串
        """
        if style == "author-year":
            # 解析作者
            authors = (
                paper.authors.split(";")[0] if ";" in paper.authors else paper.authors
            )
            # 简化作者名
            if " and " in authors:
                parts = authors.split(" and ")
                if len(parts) > 2:
                    first_author = parts[0].strip().split(",")[0]
                    return f"({first_author} et al., {paper.year})"
                else:
                    return f"({authors}, {paper.year})"
            elif "," in authors:
                last_name = authors.split(",")[0].strip()
                return f"({last_name}, {paper.year})"
            else:
                return f"({authors}, {paper.year})"
        else:
            # 编号格式
            return f"[{paper.id}]"

    def format_reference(self, paper: Paper, style: str = "nature") -> str:
        """
        生成参考文献格式

        Args:
            paper: 论文对象
            style: 格式风格 ('nature', 'apa', 'vancouver')

        Returns:
            参考文献字符串
        """
        authors = paper.authors.replace(";", ", ")

        if style == "nature":
            return f"{authors}. {paper.title}. {paper.journal} {paper.year}."
        elif style == "apa":
            return f"{authors} ({paper.year}). {paper.title}. {paper.journal}, {paper.volume}({paper.issue}), {paper.pages}."
        else:  # vancouver
            return f"{authors}. {paper.title}. {paper.journal}. {paper.year};{paper.volume}:{paper.pages}."

    def find_citations_for_text(self, text: str, limit: int = 5) -> List[Dict]:
        """
        在文本中查找并推荐相关引用

        Args:
            text: 要分析的文本
            limit: 返回数量限制

        Returns:
            推荐引用列表
        """
        # 提取关键词
        words = re.findall(r"\b[a-zA-Z]{4,}\b", text.lower())
        keywords = [
            w
            for w in words
            if w
            not in ["this", "that", "with", "from", "have", "were", "which", "about"]
        ]
        keyword_query = " ".join(set(keywords[:5]))

        # 搜索相关论文
        papers = self.search(keyword_query, limit=limit, order_by="cited_by")

        result = []
        for paper in papers:
            # 计算相关度（简单基于标题匹配）
            title_words = set(paper.title.lower().split())
            text_words = set(words)
            overlap = len(title_words & text_words)

            result.append(
                {
                    "paper": paper,
                    "in_text_citation": self.format_citation(paper),
                    "reference": self.format_reference(paper),
                    "relevance_score": overlap / len(title_words) if title_words else 0,
                }
            )

        return sorted(result, key=lambda x: x["relevance_score"], reverse=True)

    def validate_citation(
        self, citation_text: str
    ) -> Tuple[bool, Optional[Paper], str]:
        """
        验证引用是否存在

        Args:
            citation_text: 引用文本（如 "Zhang et al., 2022"）

        Returns:
            (是否存在, 对应论文, 错误信息)
        """
        # 解析引用
        patterns = [
            r"(\w+)\s+et\s+al\.,?\s+(\d{4})",  # Author et al., Year
            r"(\w+),?\s+(\d{4})",  # Author, Year
            r"\[(\d+)\]",  # [1]
        ]

        for pattern in patterns:
            match = re.search(pattern, citation_text)
            if match:
                if pattern.startswith(r"\["):
                    paper_id = int(match.group(1))
                    paper = self.get_paper_by_id(paper_id)
                else:
                    author = match.group(1)
                    year = int(match.group(2))
                    # 搜索匹配的论文
                    papers = self.search(author, limit=10, year_min=year, year_max=year)
                    if papers:
                        return True, papers[0], ""
                    else:
                        return False, None, f"未找到作者为'{author}'年份为{year}的论文"

        return False, None, "无法解析引用格式"

    def get_statistics(self) -> Dict[str, Any]:
        """获取数据库统计信息"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        stats = {}

        # 总论文数
        cursor.execute("SELECT COUNT(*) FROM papers")
        stats["total_papers"] = cursor.fetchone()[0]

        # 年份分布（排除year=0的无效数据）
        cursor.execute(
            "SELECT year, COUNT(*) FROM papers WHERE year > 0 GROUP BY year ORDER BY year"
        )
        stats["year_distribution"] = dict(cursor.fetchall())

        # 期刊分布
        cursor.execute(
            'SELECT journal, COUNT(*) FROM papers WHERE journal != "" GROUP BY journal ORDER BY COUNT(*) DESC LIMIT 10'
        )
        stats["top_journals"] = dict(cursor.fetchall())

        # 高引用论文
        cursor.execute(
            "SELECT title, cited_by FROM papers ORDER BY cited_by DESC LIMIT 5"
        )
        stats["top_cited"] = [
            {"title": r[0], "cited_by": r[1]} for r in cursor.fetchall()
        ]

        conn.close()

        return stats

    def export_to_bibtex(
        self, paper_ids: Optional[List[int]] = None, output_path: Optional[str] = None
    ) -> str:
        """
        导出为BibTeX格式

        Args:
            paper_ids: 要导出的论文ID列表，None表示全部
            output_path: 输出文件路径

        Returns:
            BibTeX内容
        """
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        if paper_ids:
            placeholders = ",".join("?" * len(paper_ids))
            cursor.execute(
                f"SELECT * FROM papers WHERE id IN ({placeholders})", paper_ids
            )
        else:
            cursor.execute("SELECT * FROM papers")

        bibtex_entries = []
        for row in cursor.fetchall():
            paper = self._row_to_paper(row)

            # 使用新的to_bibtex方法
            bibtex_entry = paper.to_bibtex()
            bibtex_entries.append(bibtex_entry)

        conn.close()

        bibtex_content = "\n\n".join(bibtex_entries)

        if output_path:
            Path(output_path).write_text(bibtex_content, encoding="utf-8")

        return bibtex_content

    def export_references_for_llm(self, paper_ids: Optional[List[int]] = None) -> str:
        """
        导出文献信息供LLM使用，包含citekey、bibtex、abstract

        Args:
            paper_ids: 要导出的论文ID列表，None表示全部

        Returns:
            格式化的文献信息字符串
        """
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        if paper_ids:
            placeholders = ",".join("?" * len(paper_ids))
            cursor.execute(
                f"SELECT * FROM papers WHERE id IN ({placeholders})", paper_ids
            )
        else:
            cursor.execute("SELECT * FROM papers")

        references = []
        for row in cursor.fetchall():
            paper = self._row_to_paper(row)
            info = paper.get_full_reference_info()

            ref_text = f"""
=== Reference ===
citekey: {info["citekey"]}

bibtex:
{info["bibtex"]}

abstract:
{info["abstract"]}
"""
            references.append(ref_text)

        conn.close()

        return "\n".join(references)

    def search_with_citekeys(
        self,
        query: str,
        limit: int = 20,
        year_min: Optional[int] = None,
        year_max: Optional[int] = None,
        journal: Optional[str] = None,
        cited_by_min: int = 0,
        order_by: str = "year",
    ) -> List[Paper]:
        """
        搜索论文并确保所有结果都有citekey

        Args:
            query: 搜索关键词
            limit: 返回数量限制
            year_min: 最早年份
            year_max: 最晚年份
            journal: 期刊名称过滤
            cited_by_min: 最少引用数
            order_by: 排序字段 (year, cited_by, title)

        Returns:
            匹配的论文列表，每篇都有生成的citekey
        """
        papers = self.search(
            query=query,
            limit=limit,
            year_min=year_min,
            year_max=year_max,
            journal=journal,
            cited_by_min=cited_by_min,
            order_by=order_by,
        )

        # 确保所有论文都有citekey
        for paper in papers:
            if not paper.citekey:
                paper.citekey = paper.generate_citekey()

        return papers

    def close(self) -> None:
        """关闭数据库连接（预留）"""
        pass


def create_literature_database(
    txt_path: str, db_path: str = "data/literature.db"
) -> LiteratureDatabaseManager:
    """
    创建文献数据库的便捷函数（从WOS TXT文件）

    Args:
        txt_path: WOS导出的Plain Text .txt文件路径
        db_path: 数据库路径

    Returns:
        文献数据库管理器实例
    """
    manager = LiteratureDatabaseManager(db_path)
    count = manager.import_from_wos_txt(txt_path)
    print(f"成功导入 {count} 篇论文到数据库")
    return manager


def create_literature_database_excel(
    excel_path: str, db_path: str = "data/literature.db"
) -> LiteratureDatabaseManager:
    """
    创建文献数据库的便捷函数（从Excel文件，保留兼容）

    Args:
        excel_path: Excel文件路径
        db_path: 数据库路径

    Returns:
        文献数据库管理器实例
    """
    manager = LiteratureDatabaseManager(db_path)
    count = manager.import_from_wos_excel(excel_path)
    print(f"成功导入 {count} 篇论文到数据库")
    return manager


if __name__ == "__main__":
    import sys

    if len(sys.argv) >= 2:
        excel_path = sys.argv[1]
        db_path = sys.argv[2] if len(sys.argv) > 2 else "data/literature.db"

        manager = create_literature_database(excel_path, db_path)
        stats = manager.get_statistics()

        print(f"\n数据库统计:")
        print(f"总论文数: {stats['total_papers']}")
        print(f"年份分布: {stats['year_distribution']}")
        print(f"Top期刊: {stats['top_journals']}")
    else:
        print("用法: python literature_db_manager.py <Excel文件路径> [数据库路径]")
