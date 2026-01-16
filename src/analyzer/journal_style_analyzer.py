"""
期刊风格分析器模块
支持参考文献格式提取和引用风格分析
"""

import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import nltk
import pdfplumber
import spacy
from nltk.corpus import stopwords
from nltk.tokenize import sent_tokenize, word_tokenize


@dataclass
class CitationStyle:
    """引用风格配置"""

    # 引用类型: "numbered" (如[1]), "author-year" (如(Smith, 2020))
    citation_type: str = "author-year"

    # 正文引用格式
    in_text_patterns: List[str] = field(default_factory=list)

    # 参考文献列表格式
    reference_format: str = "nature"  # nature, apa, vancouver, ieee

    # 示例
    example_in_text_citation: str = ""
    example_reference: str = ""

    # LaTeX命令
    latex_citation_command: str = "\\citep"  # \citep or \citet
    latex_bibliography_env: str = "thebibliography"  # thebibliography or bibliography

    def to_dict(self) -> Dict:
        return {
            "citation_type": self.citation_type,
            "in_text_patterns": self.in_text_patterns,
            "reference_format": self.reference_format,
            "example_in_text_citation": self.example_in_text_citation,
            "example_reference": self.example_reference,
            "latex_citation_command": self.latex_citation_command,
            "latex_bibliography_env": self.latex_bibliography_env,
        }


# 下载必要的NLTK数据
try:
    nltk.data.find("tokenizers/punkt")
except LookupError:
    nltk.download("punkt", quiet=True)

try:
    nltk.data.find("corpora/stopwords")
except LookupError:
    nltk.download("stopwords", quiet=True)


@dataclass
class JournalStyleReport:
    """期刊风格报告"""

    journal_name: str = ""
    analysis_date: str = ""
    papers_analyzed: int = 0

    # 词汇分析
    high_frequency_nouns: List[Tuple[str, int]] = field(default_factory=list)
    high_frequency_verbs: List[Tuple[str, int]] = field(default_factory=list)
    high_frequency_adjectives: List[Tuple[str, int]] = field(default_factory=list)
    high_frequency_adverbs: List[Tuple[str, int]] = field(default_factory=list)
    hedging_terms: List[Tuple[str, int]] = field(default_factory=list)

    # 时态分布
    tense_distribution: Dict[str, Dict[str, int]] = field(default_factory=dict)

    # 过渡词和连接词
    transition_words: Dict[str, List[Tuple[str, int]]] = field(default_factory=dict)
    conjunctions: Dict[str, List[Tuple[str, int]]] = field(
        default_factory=dict
    )  # 并列连词
    prepositions: List[Tuple[str, int]] = field(default_factory=list)  # 介词

    # 句子结构
    sentence_structure: Dict[str, any] = field(default_factory=dict)
    sentence_length_distribution: Dict[str, int] = field(
        default_factory=dict
    )  # 长短句分布
    sentence_types: Dict[str, float] = field(default_factory=dict)  # 句型比例

    # AI增强分析结果（用于8维度风格指南）
    section_style_cards: Dict[str, any] = field(default_factory=dict)

    # 各章节惯例
    section_conventions: Dict[str, Dict] = field(default_factory=dict)

    # 引用风格
    citation_style: CitationStyle = field(default_factory=CitationStyle)

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "metadata": {
                "journal_name": self.journal_name,
                "analysis_date": self.analysis_date,
                "papers_analyzed": self.papers_analyzed,
            },
            "vocabulary": {
                "high_frequency_nouns": [
                    {"term": n, "count": c} for n, c in self.high_frequency_nouns
                ],
                "high_frequency_verbs": [
                    {"term": v, "count": c} for v, c in self.high_frequency_verbs
                ],
                "high_frequency_adjectives": [
                    {"term": adj, "count": c}
                    for adj, c in self.high_frequency_adjectives
                ],
                "high_frequency_adverbs": [
                    {"term": adv, "count": c} for adv, c in self.high_frequency_adverbs
                ],
                "hedging_terms": [
                    {"term": h, "count": c} for h, c in self.hedging_terms
                ],
                "prepositions": [
                    {"term": prep, "count": c} for prep, c in self.prepositions
                ],
            },
            "tense_distribution": self.tense_distribution,
            "transition_words": {
                k: [{"term": t, "count": c} for t, c in v]
                for k, v in self.transition_words.items()
            },
            "conjunctions": {
                k: [{"term": t, "count": c} for t, c in v]
                for k, v in self.conjunctions.items()
            },
            "sentence_analysis": {
                "sentence_length_distribution": self.sentence_length_distribution,
                "sentence_types": self.sentence_types,
            },
            "sentence_structure": self.sentence_structure,
            "section_conventions": self.section_conventions,
            "citation_style": self.citation_style.to_dict(),
        }

    def save(self, path: str) -> None:
        """保存报告"""
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)


class JournalStyleAnalyzer:
    """期刊风格分析器"""

    # 常见hedging词汇
    HEDGING_TERMS = {
        "approximately",
        "roughly",
        "about",
        "suggest",
        "suggests",
        "suggested",
        "may",
        "might",
        "could",
        "would",
        "possibly",
        "perhaps",
        "probably",
        "relatively",
        "somewhat",
        "fairly",
        "rather",
        "relatively",
        "tend",
        "tends",
        "tended",
        "appear",
        "appears",
        "appeared",
        "seem",
        "seems",
        "seemed, indicate",
        "indicates",
        "indicated",
    }

    # 并列连词
    COORDINATING_CONJUNCTIONS = {"and", "but", "or", "nor", "for", "so", "yet"}

    # 从属连词
    SUBORDINATING_CONJUNCTIONS = {
        "after",
        "although",
        "as",
        "as if",
        "as long as",
        "as though",
        "because",
        "before",
        "even if",
        "even though",
        "if",
        "if only",
        "in order that",
        "now that",
        "once",
        "provided that",
        "rather than",
        "since",
        "so that",
        "than",
        "that",
        "though",
        "till",
        "unless",
        "until",
        "when",
        "whenever",
        "where",
        "whereas",
        "wherever",
        "whether",
        "while",
    }

    # 常用介词
    COMMON_PREPOSITIONS = {
        "of",
        "in",
        "to",
        "for",
        "with",
        "on",
        "at",
        "by",
        "from",
        "into",
        "during",
        "including",
        "through",
        "throughout",
        "towards",
        "upon",
        "within",
        "without",
        "among",
        "between",
        "against",
        "along",
        "around",
        "before",
        "behind",
        "beside",
        "besides",
        "beyond",
        "despite",
        "except",
        "inside",
        "onto",
        "outside",
        "since",
        "throughout",
        "under",
        "unlike",
        "until",
        "upon",
    }

    # 过渡词分类
    TRANSITION_CATEGORIES = {
        "sequential": [
            "first",
            "secondly",
            "thirdly",
            "next",
            "then",
            "subsequently",
            "finally",
            "furthermore",
            "moreover",
            "additionally",
            "besides",
            "in addition",
            "afterwards",
            "later",
            "previously",
            "before",
        ],
        "contrastive": [
            "however",
            "nevertheless",
            "nonetheless",
            "although",
            "though",
            "despite",
            "in contrast",
            "conversely",
            "on the other hand",
            "while",
            "whereas",
            "but",
            "yet",
            "otherwise",
        ],
        "additive": [
            "furthermore",
            "moreover",
            "additionally",
            "besides",
            "also",
            "likewise",
            "similarly",
            "in the same way",
            "equally",
        ],
        "causal": [
            "therefore",
            "thus",
            "hence",
            "consequently",
            "as a result",
            "because",
            "due to",
            "owing to",
            "for this reason",
            "accordingly",
        ],
        "exemplifying": [
            "for example",
            "for instance",
            "specifically",
            "namely",
            "in particular",
            "particularly",
            "such as",
            "namely",
        ],
    }

    def __init__(self, language: str = "english"):
        """
        初始化分析器

        Args:
            language: 语言 ('english' 或 'chinese')
        """
        self.language = language
        self.nlp = spacy.load("en_core_web_sm")
        self.stop_words = set(stopwords.words("english"))

        # 章节定义：标准学术论文的所有可能章节
        self.SECTION_DEFINITIONS = {
            "abstract": {
                "patterns": [
                    r"(?:^|\n)\s*(?:abstract|summary)[\s:]*\n*",
                    r"^\s*(?:1\.)?\s*(?:abstract|summary)[\s.]*$",
                ],
                "end_patterns": [
                    r"(?:^|\n)\s*(?:\d+\.?\s*)?(?:introduction|1\.?\s*(?:introduction|background))",
                    r"(?:^|\n)\s*(?:keywords)[\s:]*",
                ],
            },
            "introduction": {
                "patterns": [
                    r"(?:^|\n)\s*(?:\d+\.?\s*)?(?:introduction|background)[\s:]*\n*",
                    r"(?:^|\n)\s*1\.?\s*(?:introduction|background)[\s.]*$",
                ],
                "end_patterns": [
                    r"(?:^|\n)\s*(?:\d+\.?\s*)?(?:methods|materials\s*(?:and\s*)?methods?|methodology)",
                    r"(?:^|\n)\s*2\.?\s*(?:methods|materials|methodology)",
                    r"(?:^|\n)\s*(?:\d+\.?\s*)?study\s*area",
                ],
            },
            "materials": {
                "patterns": [
                    r"(?:^|\n)\s*(?:\d+\.?\s*)?(?:materials|materials\s*and\s*methods|methods|methodology)[\s:]*\n*",
                    r"(?:^|\n)\s*2\.?\s*(?:materials|methods|methodology)[\s.]*$",
                ],
                "end_patterns": [
                    r"(?:^|\n)\s*(?:\d+\.?\s*)?(?:results|findings|outcome)",
                    r"(?:^|\n)\s*3\.?\s*(?:results|findings)",
                    r"(?:^|\n)\s*(?:\d+\.?\s*)?data\s*analysis",
                ],
            },
            "methods": {
                "patterns": [
                    r"(?:^|\n)\s*(?:\d+\.?\s*)?(?:methods|methodology|experimental\s*design|procedures)[\s:]*\n*",
                    r"(?:^|\n)\s*2\.?\s*(?:methods|methodology|procedures)[\s.]*$",
                ],
                "end_patterns": [
                    r"(?:^|\n)\s*(?:\d+\.?\s*)?(?:results|findings|outcome)",
                    r"(?:^|\n)\s*3\.?\s*(?:results|findings)",
                    r"(?:^|\n)\s*(?:\d+\.?\s*)?data\s*analysis",
                ],
            },
            "results": {
                "patterns": [
                    r"(?:^|\n)\s*(?:\d+\.?\s*)?(?:results|findings|outcome|observations)[\s:]*\n*",
                    r"(?:^|\n)\s*3\.?\s*(?:results|findings|observations)[\s.]*$",
                ],
                "end_patterns": [
                    r"(?:^|\n)\s*(?:\d+\.?\s*)?(?:discussion|interpretations?)",
                    r"(?:^|\n)\s*4\.?\s*(?:discussion|interpretations?)",
                    r"(?:^|\n)\s*(?:\d+\.?\s*)?commentary",
                ],
            },
            "discussion": {
                "patterns": [
                    r"(?:^|\n)\s*(?:\d+\.?\s*)?(?:discussion|interpretations?|comments?)[\s:]*\n*",
                    r"(?:^|\n)\s*4\.?\s*(?:discussion|interpretations?)[\s.]*$",
                ],
                "end_patterns": [
                    r"(?:^|\n)\s*(?:\d+\.?\s*)?(?:conclusion|conclusions|summary)",
                    r"(?:^|\n)\s*5\.?\s*(?:conclusion|conclusions|summary)",
                    r"(?:^|\n)\s*(?:\d+\.?\s*)?(?:final\s*remarks|final\s*comments)",
                ],
            },
            "conclusion": {
                "patterns": [
                    r"(?:^|\n)\s*(?:\d+\.?\s*)?(?:conclusion|conclusions|summary|concluding\s*remarks)[\s:]*\n*",
                    r"(?:^|\n)\s*5\.?\s*(?:conclusion|conclusions|summary)[\s.]*$",
                ],
                "end_patterns": [
                    r"(?:^|\n)\s*(?:\d+\.?\s*)?(?:references?|bibliography|acknowledgements)",
                    r"(?:^|\n)\s*(?:\[\d+\]\s*)?references?",
                    r"(?:^|\n)\s*acknowledgements?",
                    r"(?:^|\n)\s*appendix",
                    r"(?:^|\n)\s*supplementary",
                ],
            },
            "acknowledgements": {
                "patterns": [
                    r"(?:^|\n)\s*(?:acknowledgements?|acknowledgments?|thanks?)[\s:]*\n*",
                    r"(?:^|\n)\s*acknowledgements?[\s.]*$",
                ],
                "end_patterns": [
                    r"(?:^|\n)\s*(?:\d+\.?\s*)?(?:references?|bibliography)",
                    r"(?:^|\n)\s*appendix",
                    r"(?:^|\n)\s*supplementary",
                ],
            },
            "references": {
                "patterns": [
                    # 匹配带编号的: [1] REFERENCES, [1] References
                    r"(?:^|\n)\s*\[\d+\]\s*(?:references?|bibliography)[\s:]*",
                    # 匹配纯REFERENCES (大写或小写)，可能带有冒号或空格
                    r"(?:^|\n)\s*(?:references?|bibliography|reference\s*list)[\s:]*",
                    # 匹配单独一行的REFERENCES
                    r"(?:^|\n)\s*(?:references?)[\s.]*(?=\n|$)",
                    # 中文
                    r"(?:^|\n)\s*参考文献[\s:]*",
                ],
                "end_patterns": [
                    r"(?:^|\n)\s*appendix",
                    r"(?:^|\n)\s*supplementary",
                    r"(?:^|\n)\s*acknowledgements?",
                    r"(?:^|\n)\s*作者信息",
                    r"(?:^|\n)\s*author\s*information",
                ],
            },
            "appendix": {
                "patterns": [
                    r"(?:^|\n)\s*(?:appendix|appendices|supplementary\s*(?:material|information|files?))[\s:]*\n*",
                    r"(?:^|\n)\s*appendix[\s.]*$",
                    r"(?:^|\n)\s*supplementary[\s.]*$",
                ],
                "end_patterns": [
                    r"(?:^|\n)\s*(?:appendix|appendices|supplementary)",
                ],
            },
        }

    def extract_sections(self, text: str) -> Dict[str, str]:
        """
        按章节提取文本

        Args:
            text: 论文全文

        Returns:
            章节名称到章节文本的映射
        """
        sections = {}
        text_lower = text.lower()
        text_original = text

        # 标准化文本用于查找（保留原始文本用于提取）
        # 先尝试用正则表达式匹配章节标题

        # 定义所有章节的起始位置
        section_starts = []

        for section_name, config in self.SECTION_DEFINITIONS.items():
            for pattern in config["patterns"]:
                for match in re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE):
                    section_starts.append((match.start(), section_name, match.group(0)))

        # 按起始位置排序
        section_starts.sort(key=lambda x: x[0])

        # 合并相邻的同一章节
        merged_starts = []
        for start, name, header in section_starts:
            if (
                merged_starts
                and merged_starts[-1][1] == name
                and start - merged_starts[-1][0] < 50
            ):
                # 同一章节，相距很近，保留第一个
                continue
            merged_starts.append((start, name, header))

        # 提取每个章节的内容
        for i, (start, section_name, header) in enumerate(merged_starts):
            # 确定章节结束位置
            config = self.SECTION_DEFINITIONS[section_name]
            end_pos = len(text)

            for next_start, _, _ in merged_starts[i + 1 :]:
                # 找到下一个章节的起始位置
                if next_start > start:
                    end_pos = next_start
                    break

            # 应用结束模式进一步裁剪
            for end_pattern in config["end_patterns"]:
                match = re.search(end_pattern, text[start:end_pos], re.IGNORECASE)
                if match:
                    # 在匹配位置之前截断
                    end_pos = start + match.start()
                    break

            # 提取章节内容
            section_content = text[start:end_pos].strip()
            if section_content and len(section_content) > 50:  # 过滤掉太短的误匹配
                sections[section_name] = section_content

        return sections

    def chunk_by_sections(self, text: str) -> Dict[str, List[str]]:
        """
        按章节切分文本，每个章节内部按段落分块

        Args:
            text: 论文全文

        Returns:
            章节名称到chunk列表的映射
        """
        sections = self.extract_sections(text)
        chunks_by_section = {}

        for section_name, section_text in sections.items():
            section_chunks = self._chunk_text_by_paragraphs(
                section_text, max_chars=30000
            )
            chunks_by_section[section_name] = section_chunks

        return chunks_by_section

    def _chunk_text_by_paragraphs(self, text: str, max_chars: int = 30000) -> List[str]:
        """
        按段落分块（辅助方法）

        Args:
            text: 文本
            max_chars: 每个chunk的最大字符数

        Returns:
            chunk列表
        """
        chunks = []

        if len(text) <= max_chars:
            return [text]

        # 按段落分割
        paragraphs = text.split("\n\n")
        current_chunk = ""

        for paragraph in paragraphs:
            if len(current_chunk + paragraph) < max_chars:
                current_chunk += paragraph + "\n\n"
            else:
                if current_chunk.strip():
                    chunks.append(current_chunk.strip())
                current_chunk = paragraph + "\n\n"

        if current_chunk.strip():
            chunks.append(current_chunk.strip())

        return chunks

    def analyze_by_sections(
        self, text: str, section_name: str = "general"
    ) -> Dict[str, Any]:
        """
        按章节分析文本风格

        Args:
            text: 文本
            section_name: 章节名称

        Returns:
            分析结果
        """
        # 先按章节分块
        chunks_by_section = self.chunk_by_sections(text)

        # 分析每个章节
        all_results = {}

        for sec_name, chunks in chunks_by_section.items():
            # references章节不进行写作风格分析，只提取引用格式
            if sec_name == "references":
                reference_format = self._analyze_reference_format("\n\n".join(chunks))
                all_results["references"] = {
                    "reference_format": reference_format,
                    "citation_examples": self._extract_citation_examples(text),
                }
                continue

            section_results = []

            for i, chunk in enumerate(chunks):
                try:
                    doc = self.nlp(chunk)
                    chunk_result = self._analyze_chunk(doc, sec_name)
                    section_results.append(chunk_result)

                    # 清理内存
                    del doc
                    import gc

                    gc.collect()

                except Exception as e:
                    print(f"分析章节 {sec_name} 的 chunk {i + 1} 时出错: {e}")
                    continue

            # 合并章节内所有chunk的结果
            if section_results:
                merged = self._merge_section_results(section_results)
                all_results[sec_name] = merged

        return all_results

    def _analyze_reference_format(self, references_text: str) -> Dict[str, Any]:
        """
        分析参考文献格式

        Args:
            references_text: 参考文献全文

        Returns:
            参考文献格式分析结果
        """
        if not references_text.strip():
            return {"format": "unknown", "examples": []}

        lines = references_text.split("\n")
        valid_refs = []
        for line in lines:
            line = line.strip()
            # 过滤掉标题行和太短的行
            if len(line) > 20 and not re.match(
                r"^(references?|bibliography|reference\s*list|\[\d+\]|参考文献)",
                line,
                re.IGNORECASE,
            ):
                valid_refs.append(line)

        if not valid_refs:
            return {"format": "unknown", "examples": []}

        # 判断格式类型
        format_type = self._determine_reference_format("\n".join(valid_refs[:20]))

        return {
            "format": format_type,
            "examples": valid_refs[:5],  # 保存5个示例
            "total_entries": len(valid_refs),
        }

    def _extract_citation_examples(self, full_text: str) -> List[Dict[str, str]]:
        """
        从正文中提取引用示例

        Args:
            full_text: 论文全文

        Returns:
            引用示例列表
        """
        examples = []

        # 编号格式: [1], [1,2], [1-3]
        numbered_patterns = [
            r"\[(\d+(?:[\s,/-]+\d+)*)\]",
        ]

        # 作者-年份格式: (Smith, 2020), (Smith et al., 2020)
        author_year_patterns = [
            r"\(([A-Z][a-zA-Z'-]+(?:\s+et\s+al\.?)?,\s*\d{4}[a-z]?\)",
            r"([A-Z][a-zA-Z'-]+(?:\s+et\s+al\.?)?\s+\(\d{4}[a-z]?\))",
        ]

        for pattern in numbered_patterns:
            for match in re.finditer(pattern, full_text):
                examples.append(
                    {
                        "type": "numbered",
                        "text": match.group(0),
                        "key": match.group(1) if match.lastindex else "",
                    }
                )

        for pattern in author_year_patterns:
            for match in re.finditer(pattern, full_text):
                examples.append(
                    {
                        "type": "author-year",
                        "text": match.group(0),
                    }
                )

        return examples[:20]  # 限制数量

    def _merge_section_results(self, results: List[Dict]) -> Dict:
        """合并章节内多个chunk的分析结果"""
        merged = {
            "vocabulary": {
                "nouns": {},
                "verbs": {},
                "adjectives": {},
                "adverbs": {},
            },
            "sentence_structure": {
                "avg_sentence_length": [],
                "sentence_count": 0,
                "total_tokens": 0,
            },
            "stylistic_features": {
                "passive_voice_ratio": [],
                "token_count": 0,
            },
        }

        for result in results:
            # 合并词汇
            for category in ["nouns", "verbs", "adjectives", "adverbs"]:
                if category in result.get("vocabulary", {}):
                    for word, freq in result["vocabulary"][category].items():
                        merged["vocabulary"][category][word] = (
                            merged["vocabulary"][category].get(word, 0) + freq
                        )

            # 合并句子结构
            if "sentence_structure" in result:
                ss = result["sentence_structure"]
                if "avg_sentence_length" in ss:
                    merged["sentence_structure"]["avg_sentence_length"].append(
                        ss["avg_sentence_length"]
                    )
                merged["sentence_structure"]["sentence_count"] += ss.get(
                    "sentence_count", 0
                )
                merged["sentence_structure"]["total_tokens"] += ss.get(
                    "total_tokens", 0
                )

            # 合并文体特征
            if "stylistic_features" in result:
                sf = result["stylistic_features"]
                if "passive_voice_ratio" in sf:
                    merged["stylistic_features"]["passive_voice_ratio"].append(
                        sf["passive_voice_ratio"]
                    )
                merged["stylistic_features"]["token_count"] += sf.get("token_count", 0)

        # 计算平均值
        if merged["sentence_structure"]["avg_sentence_length"]:
            lengths = merged["sentence_structure"]["avg_sentence_length"]
            merged["sentence_structure"]["avg_sentence_length"] = sum(lengths) / len(
                lengths
            )

        if merged["stylistic_features"]["passive_voice_ratio"]:
            ratios = merged["stylistic_features"]["passive_voice_ratio"]
            merged["stylistic_features"]["passive_voice_ratio"] = sum(ratios) / len(
                ratios
            )

        return merged

    def extract_references_section(self, pdf_path: Path) -> str:
        """
        从PDF中提取参考文献部分

        Args:
            pdf_path: PDF文件路径

        Returns:
            参考文献部分的纯文本
        """
        if pdf_path.suffix.lower() == ".pdf":
            with pdfplumber.open(pdf_path) as pdf:
                full_text = ""
                for page in pdf.pages:
                    text = page.extract_text() or ""
                    full_text += text + "\n"
        elif pdf_path.suffix.lower() in [".txt", ".md"]:
            full_text = pdf_path.read_text(encoding="utf-8")
        else:
            return ""

        # 查找参考文献部分的开始位置
        ref_patterns = [
            r"(?:^|\n)\s*references?\s*(?:\[:\]|\[::\])?\s*$",
            r"(?:^|\n)\s*references?\s*:\s*$",
            r"(?:^|\n)\s*bibliography\s*(?:\[:\]|\[::\])?\s*$",
            r"(?:^|\n)\s*reference\s*list\s*$",
            r"(?:^|\n)\s*\[\d+\]\s*references?\s*$",
            r"(?:^|\n)\s*\[\d+\]\s*bibliography\s*$",
            # 中文
            r"(?:^|\n)\s*参考文献\s*$",
        ]

        ref_start = -1
        for pattern in ref_patterns:
            match = re.search(pattern, full_text, re.MULTILINE | re.IGNORECASE)
            if match:
                ref_start = match.start()
                break

        if ref_start == -1:
            return ""

        # 提取参考文献部分（到文档结束或附录之前）
        ref_text = full_text[ref_start:]

        # 截断到附录或文档结束
        end_patterns = [
            r"\n\s*appendix\b",
            r"\n\s*supplementary\s*material\b",
            r"\n\s*supplementary\s*information\b",
            r"\n\s*acknowledgements?\b",
            r"\n\s*致谢\b",
            r"\n\s*附录\b",
        ]

        for pattern in end_patterns:
            match = re.search(pattern, ref_text, re.IGNORECASE)
            if match:
                ref_text = ref_text[: match.start()]
                break

        return ref_text.strip()

    def analyze_citation_style(self, pdf_path: Path) -> CitationStyle:
        """
        分析PDF中的引用风格

        Args:
            pdf_path: PDF文件路径

        Returns:
            CitationStyle对象
        """
        style = CitationStyle()

        # 提取全文用于正文引用分析
        if pdf_path.suffix.lower() == ".pdf":
            with pdfplumber.open(pdf_path) as pdf:
                full_text = ""
                for page in pdf.pages:
                    text = page.extract_text() or ""
                    full_text += text + "\n"
        elif pdf_path.suffix.lower() in [".txt", ".md"]:
            full_text = pdf_path.read_text(encoding="utf-8")
        else:
            return style

        # 分析正文引用格式
        # 编号格式: [1], [1,2], [1-3], [1,2,4-6]
        numbered_patterns = [
            r"\[\d+\]",
            r"\[\d+\s*,\s*\d+\]",
            r"\[\d+\s*-\s*\d+\]",
            r"\[\d+\s*,\s*\d+\s*-\s*\d+\]",
        ]

        # 作者-年份格式: (Smith, 2020), (Smith et al., 2020), Smith (2020)
        author_year_patterns = [
            r"\([A-Z][a-zA-Z'-]+\s+et\s+al\.?,\s*\d{4}\)",
            r"\([A-Z][a-zA-Z'-]+,\s+\d{4}\)",
            r"\([A-Z][a-zA-Z'-]+\s+and\s+[A-Z][a-zA-Z'-]+,\s*\d{4}\)",
            r"[A-Z][a-zA-Z'-]+\s+\(\d{4}\)",
            r"[A-Z][a-zA-Z'-]+\s+et\s+al\.?\s+\(\d{4}\)",
        ]

        # 统计各类引用的出现次数
        numbered_count = 0
        author_year_count = 0

        for pattern in numbered_patterns:
            numbered_count += len(re.findall(pattern, full_text))

        for pattern in author_year_patterns:
            author_year_count += len(re.findall(pattern, full_text))

        # 判断引用类型
        if numbered_count > author_year_count:
            style.citation_type = "numbered"
            style.latex_citation_command = "\\citep"
            style.latex_bibliography_env = "thebibliography"
        else:
            style.citation_type = "author-year"
            style.latex_citation_command = "\\citep"
            style.latex_bibliography_env = "thebibliography"

        # 提取示例引用
        example_patterns = {
            "numbered": r"\[\d+\](?:,\s*\[\d+\])*(?:;\s*\[\d+\](?:,\s*\[\d+\])*)*",
            "author_year": r"\([A-Z][a-zA-Z'-]+(?:\s+et\s+al\.?)?,\s*\d{4}\)",
            "narrative": r"[A-Z][a-zA-Z'-]+(?:\s+et\s+al\.?)?\s+\(\d{4}\)",
        }

        for key, pattern in example_patterns.items():
            match = re.search(pattern, full_text)
            if match:
                example = match.group(0).strip()
                if key == "numbered":
                    style.example_in_text_citation = example
                elif key == "author_year":
                    style.example_in_text_citation = example

        # 分析参考文献列表格式
        refs_text = self.extract_references_section(pdf_path)
        if refs_text:
            style.reference_format = self._determine_reference_format(refs_text)

            # 提取示例参考文献
            lines = refs_text.split("\n")
            for line in lines[:10]:  # 检查前10行
                line = line.strip()
                if len(line) > 20 and len(line) < 500:
                    # 排除标题行
                    if not re.match(
                        r"^(references?|bibliography|reference\s*list|\[\d+\]|参考文献)",
                        line,
                        re.IGNORECASE,
                    ):
                        style.example_reference = line
                        break

        return style

    def _determine_reference_format(self, ref_text: str) -> str:
        """
        根据参考文献列表文本判断格式类型

        Args:
            ref_text: 参考文献列表文本

        Returns:
            格式类型: "nature", "apa", "vancouver", "ieee"
        """
        # Nature格式: Authors. Title. Journal Year.
        nature_pattern = r"^[A-Z][a-zA-Z'-]+.*\.\s+[A-Z][a-zA-Z0-9].*\.\s+\d{4}\."

        # APA格式: Authors (Year). Title. Journal, Volume(Issue), Pages.
        apa_pattern = (
            r"^[A-Z][a-zA-Z'-]+.*\s+\(\d{4}\)\.\s+.*\.\s+[A-Z][a-zA-Z0-9].*,\s+\d+"
        )

        # Vancouver格式: Authors. Title. Journal. Year;Volume:Pages.
        vancouver_pattern = r"^[A-Z][a-zA-Z'-]+.*\.\s+[A-Z][a-zA-Z0-9].*\.\s+\d{4};\d+"

        # IEEE格式: Authors, "Title," Journal, vol, pp, Year.
        ieee_pattern = r"^[A-Z][a-zA-Z'-]+,\s*\""

        # 检查各格式的出现频率
        counts = {"nature": 0, "apa": 0, "vancouver": 0, "ieee": 0}

        lines = ref_text.split("\n")
        for line in lines:
            line = line.strip()
            if re.match(nature_pattern, line):
                counts["nature"] += 1
            if re.match(apa_pattern, line):
                counts["apa"] += 1
            if re.match(vancouver_pattern, line):
                counts["vancouver"] += 1
            if re.match(ieee_pattern, line):
                counts["ieee"] += 1

        # 返回最常见的格式
        if max(counts.values()) == 0:
            return "nature"  # 默认使用Nature格式

        return max(counts, key=counts.get)

    def analyze_papers(
        self, paper_paths: List[Path], journal_name: str = "Target Journal"
    ) -> JournalStyleReport:
        """
        分析多篇论文

        Args:
            paper_paths: PDF文件路径列表
            journal_name: 期刊名称

        Returns:
            完整的风格分析报告
        """
        from datetime import datetime

        report = JournalStyleReport()
        report.journal_name = journal_name
        report.analysis_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        report.papers_analyzed = len(paper_paths)

        # 分析引用风格
        citation_styles = []
        for paper_path in paper_paths:
            try:
                style = self.analyze_citation_style(paper_path)
                citation_styles.append(style)
            except Exception as e:
                print(f"分析 {paper_path.name} 的引用风格时出错: {e}")

        # 综合引用风格（取众数）
        if citation_styles:
            report.citation_style = self._merge_citation_styles(citation_styles)

        # 聚合所有分析结果
        all_nouns = Counter()
        all_verbs = Counter()
        all_adjectives = Counter()
        all_adverbs = Counter()
        all_prepositions = Counter()
        all_hedging = Counter()
        all_tense = defaultdict(list)
        all_transitions = defaultdict(list)
        all_conjunctions = defaultdict(list)
        all_sentence_lengths = []
        all_sentence_length_distributions = defaultdict(list)
        all_sentence_types = defaultdict(list)
        passive_ratios = []

        for paper_path in paper_paths:
            sections = self.extract_text_from_pdf(paper_path)

            for section, text in sections.items():
                if not text.strip():
                    continue

                analysis = self.analyze_text(text, section)

                # 聚合词汇
                all_nouns.update(analysis.get("nouns", {}))
                all_verbs.update(analysis.get("verbs", {}))
                all_adjectives.update(analysis.get("adjectives", {}))
                all_adverbs.update(analysis.get("adverbs", {}))
                all_prepositions.update(analysis.get("prepositions", {}))

                # Hedging词汇
                for word in self.HEDGING_TERMS:
                    count = text.lower().count(word)
                    if count > 0:
                        all_hedging[word] += count

                # 时态分布
                tense = analysis.get("tense_distribution", {})
                if tense:
                    section_key = section if section != "general" else "general"
                    all_tense[section_key].append(tense)

                # 过渡词
                transitions = analysis.get("transition_counts", {})
                for cat, count in transitions.items():
                    all_transitions[cat] = all_transitions.get(cat, 0) + count

                # 连词
                conjunctions = analysis.get("conjunction_counts", {})
                for cat, count in conjunctions.items():
                    all_conjunctions[cat] = all_conjunctions.get(cat, 0) + count

                # 句子长度
                all_sentence_lengths.append(analysis.get("avg_sentence_length", 0))

                # 句子长度分布
                length_dist = analysis.get("sentence_length_distribution", {})
                for dist_type, ratio in length_dist.items():
                    all_sentence_length_distributions[dist_type].append(ratio)

                # 句型分布
                sentence_types = analysis.get("sentence_types", {})
                for sent_type, ratio in sentence_types.items():
                    all_sentence_types[sent_type].append(ratio)

                # 被动语态
                passive_ratios.append(analysis.get("passive_ratio", 0))

        # 计算平均值
        report.high_frequency_nouns = all_nouns.most_common(50)
        report.high_frequency_verbs = all_verbs.most_common(30)
        report.high_frequency_adjectives = all_adjectives.most_common(40)
        report.high_frequency_adverbs = all_adverbs.most_common(40)
        report.prepositions = all_prepositions.most_common(40)
        report.hedging_terms = all_hedging.most_common(20)

        # 时态分布（按章节平均）
        for section, pcts in all_tense.items():
            if pcts:
                avg_pcts = {
                    "past": round(sum(p["past"] for p in pcts) / len(pcts), 2),
                    "present": round(sum(p["present"] for p in pcts) / len(pcts), 2),
                    "future": round(sum(p["future"] for p in pcts) / len(pcts), 2),
                }
                report.tense_distribution[section] = avg_pcts

        # 过渡词
        for cat, count in all_transitions.items():
            report.transition_words[cat] = [(cat, count)]

        # 连词
        for cat, count in all_conjunctions.items():
            report.conjunctions[cat] = [(cat, count)]

        # 句子结构
        avg_length = (
            sum(all_sentence_lengths) / len(all_sentence_lengths)
            if all_sentence_lengths
            else 0
        )
        avg_passive = sum(passive_ratios) / len(passive_ratios) if passive_ratios else 0

        # 句子长度分布平均值
        sentence_length_dist_avg = {}
        for dist_type in ["short", "medium", "long"]:
            if dist_type in all_sentence_length_distributions:
                ratios = all_sentence_length_distributions[dist_type]
                sentence_length_dist_avg[dist_type] = (
                    round(sum(ratios) / len(ratios), 3) if ratios else 0
                )

        # 句型分布平均值
        sentence_types_avg = {}
        for sent_type in ["simple", "compound", "complex"]:
            if sent_type in all_sentence_types:
                ratios = all_sentence_types[sent_type]
                sentence_types_avg[sent_type] = (
                    round(sum(ratios) / len(ratios), 3) if ratios else 0
                )

        report.sentence_structure = {
            "average_sentence_length": round(avg_length, 2),
            "passive_voice_ratio": round(avg_passive, 2),
            "papers_analyzed": len(paper_paths),
        }

        report.sentence_length_distribution = sentence_length_dist_avg
        report.sentence_types = sentence_types_avg

        return report

    def _merge_citation_styles(self, styles: List[CitationStyle]) -> CitationStyle:
        """
        合并多个引用风格，取最常见的值
        """
        if not styles:
            return CitationStyle()

        merged = CitationStyle()

        # 统计各类型的出现次数
        citation_types = Counter([s.citation_type for s in styles])
        ref_formats = Counter([s.reference_format for s in styles])

        # 选择最常见的类型
        if citation_types:
            merged.citation_type = citation_types.most_common(1)[0][0]

        if ref_formats:
            merged.reference_format = ref_formats.most_common(1)[0][0]

        # 设置LaTeX命令
        if merged.citation_type == "numbered":
            merged.latex_citation_command = "\\citep"
        else:
            merged.latex_citation_command = "\\citep"

        # 收集示例
        for style in styles:
            if style.example_in_text_citation and not merged.example_in_text_citation:
                merged.example_in_text_citation = style.example_in_text_citation
            if style.example_reference and not merged.example_reference:
                merged.example_reference = style.example_reference

        return merged

    def extract_text_from_pdf(self, pdf_path: Path) -> Dict[str, str]:
        """
        从PDF或文本文件提取各章节文本

        Args:
            pdf_path: PDF或文本文件路径

        Returns:
            按章节分组的文本字典
        """
        sections = {"introduction": "", "methods": "", "results": "", "discussion": ""}

        # 根据文件扩展名选择处理方式
        if pdf_path.suffix.lower() == ".pdf":
            with pdfplumber.open(pdf_path) as pdf:
                full_text = ""
                for page in pdf.pages:
                    text = page.extract_text() or ""
                    full_text += text + "\n"
        elif pdf_path.suffix.lower() in [".txt", ".md"]:
            full_text = pdf_path.read_text(encoding="utf-8")
        else:
            raise ValueError(f"不支持的文件格式: {pdf_path.suffix}")

        # 简单基于标题的分段（改进版本，支持多种格式）
        text_lower = full_text.lower()

        # 识别各章节 - 改进的正则表达式
        section_patterns = {
            "abstract": r"(?:^|\n)\s*(?:abstract|summary)[\s:]*\n*(.+?)(?=(?:1\.?\s*|introduction|background|methods))",
            "introduction": r"(?:^|\n)\s*(?:1\.?\s*|introduction|background)[\s:]*\n*(.+?)(?=(?:2\.?\s*|methods|materials and methods|results))",
            "methods": r"(?:^|\n)\s*(?:2\.?\s*|methods|materials and methods)[\s:]*\n*(.+?)(?=(?:3\.?\s*|results|discussion|conclusion))",
            "results": r"(?:^|\n)\s*(?:3\.?\s*|results)[\s:]*\n*(.+?)(?=(?:4\.?\s*|discussion|conclusion|methods))",
            "discussion": r"(?:^|\n)\s*(?:4\.?\s*|discussion)[\s:]*\n*(.+?)(?=(?:5\.?\s*|conclusion|final\s*remarks|references|acknowledgements))",
            "conclusion": r"(?:^|\n)\s*(?:5\.?\s*|conclusion|final\s*remarks|conclusions?)[\s:]*\n*(.+?)(?=\n\s*(?:references|bibliography|acknowledgements|appendix|reference\s*list|后记|致谢|$))",
        }

        for section, pattern in section_patterns.items():
            try:
                match = re.search(pattern, text_lower, re.DOTALL | re.IGNORECASE)
                if match:
                    # 从原始文本中提取（保留大小写）
                    matched_text = match.group(1).strip()
                    # 尝试在原始文本中找到对应位置
                    original_match = re.search(
                        re.escape(match.group(0).lower()),
                        full_text.lower(),
                        re.DOTALL | re.IGNORECASE,
                    )
                    if original_match:
                        sections[section] = full_text[
                            original_match.start() : original_match.end()
                        ].strip()
                    else:
                        sections[section] = matched_text
            except Exception as e:
                print(f"Error extracting {section}: {e}")
                continue

        # 如果某些章节为空，尝试基于关键词的备用方法
        fallback_patterns = {
            "abstract": r"(?:abstract|summary)[\s\n]+(.+?)(?=\n\s*\d+\s|\n\s*introduction|\n\s*background)",
            "introduction": r"(?:introduction|background)[\s\n]+(.+?)(?=\n\s*\d+\s|\n\s*methods|\n\s*materials)",
            "methods": r"(?:methods|materials)[\s\n]+(.+?)(?=\n\s*\d+\s|\n\s*results|\n\s*discussion)",
            "results": r"(?:results|findings)[\s\n]+(.+?)(?=\n\s*\d+\s|\n\s*discussion|\n\s*conclusion)",
            "discussion": r"(?:discussion|interpretations?)[\s\n]+(.+?)(?=\n\s*\d+\s|\n\s*conclusion|\n\s*final)",
            "conclusion": r"(?:conclusion|conclusions|final\s*remarks|concl[\.]?\s*(?:\d+)?)[\s\n:]*([^\n]+(?:(?!\n\s*(?:\[\d+\]\s*)?references?\b|\n\s*(?:\[\d+\]\s*)?bibliography|\n\s*acknowledgements|\n\s*reference\s+list|\n\s*appendix|\n\s*$\n).)*)",
        }

        for section in sections:
            if not sections[section] or len(sections[section]) < 100:
                # 尝试备用模式
                try:
                    fallback_match = re.search(
                        fallback_patterns[section],
                        text_lower,
                        re.DOTALL | re.IGNORECASE,
                    )
                    if fallback_match:
                        matched_text = fallback_match.group(1).strip()
                        original_match = re.search(
                            re.escape(fallback_match.group(0).lower()),
                            full_text.lower(),
                            re.DOTALL | re.IGNORECASE,
                        )
                        if original_match:
                            sections[section] = full_text[
                                original_match.start() : original_match.end()
                            ].strip()
                        else:
                            sections[section] = matched_text
                except:
                    continue

        # 后处理：严格截断conclusion到References之前
        conclusion_text = sections.get("conclusion", "")
        if conclusion_text:
            # 查找References的多种写法（更全面的模式）
            ref_patterns = [
                # 带方括号编号的
                r"\n\s*\[\d+\]\s*references?\b",
                r"\n\s*\[\d+\]\s*bibliography",
                r"\n\s*\[\d+\]\s*reference",
                # 不带编号的
                r"\n\s*(?:the\s+)?references?\s*(?:\[:\]|\[::\]|$)",
                r"\n\s*(?:the\s+)?bibliography\b",
                r"\n\s*(?:the\s+)?reference\s+list\b",
                r"\n\s*acknowledgements?\b",
                r"\n\s*appendix\b",
                r"\n\s*supplementary\s*material\b",
                r"\n\s*supplementary\s*information\b",
                # 中文
                r"\n\s*参考文献\b",
                r"\n\s*致谢\b",
                r"\n\s*附录\b",
                # 单行References
                r"^references?\s*$",
                r"^reference\s+list\s*$",
            ]

            found_ref = False
            for ref_pat in ref_patterns:
                ref_match = re.search(
                    ref_pat, conclusion_text, re.IGNORECASE | re.MULTILINE
                )
                if ref_match:
                    # 截断到References之前
                    sections["conclusion"] = conclusion_text[
                        : ref_match.start()
                    ].strip()
                    print(
                        f"  Truncated conclusion at reference marker, length: {len(sections['conclusion'])}"
                    )
                    found_ref = True
                    break

            # 如果还是太长（超过5000字符），尝试找最后一个段落
            if not found_ref and len(conclusion_text) > 5000:
                # 找到最后一个完整段落
                paragraphs = conclusion_text.split("\n\n")
                # 移除最后一个可能是reference的段落
                for i in range(len(paragraphs) - 1, -1, -1):
                    para = paragraphs[i].strip()
                    # 如果这个段落看起来像reference，跳过
                    if (
                        re.match(r"^\[\d+\]|^[A-Z][a-z]+,\s*\d{4}|^\s*\d+\.\s+", para)
                        and len(para) < 500
                    ):
                        continue
                    # 否则这就是最后一个段落
                    last_valid_idx = i
                    break
                else:
                    last_valid_idx = len(paragraphs) - 1

                # 截取到最后一个有效段落
                truncated = "\n\n".join(paragraphs[: last_valid_idx + 1])
                if len(truncated) < len(conclusion_text):
                    sections["conclusion"] = truncated
                    print(
                        f"  Truncated conclusion to last valid paragraph, length: {len(sections['conclusion'])}"
                    )

        return sections

    def analyze_text(self, text: str, section: str = "general") -> Dict:
        """
        分析单段文本的风格特征 - 添加内存管理和文本分块处理

        Args:
            text: 文本
            section: 文本所属章节

        Returns:
            风格分析结果
        """
        if not text.strip():
            return {}

        # 文本分块处理以避免内存问题
        max_chunk_size = 30000  # 减小chunk大小以避免内存问题
        chunks = []

        if len(text) > max_chunk_size:
            # 按段落分割长文本
            paragraphs = text.split("\n\n")
            current_chunk = ""

            for paragraph in paragraphs:
                if len(current_chunk + paragraph) < max_chunk_size:
                    current_chunk += paragraph + "\n\n"
                else:
                    if current_chunk.strip():
                        chunks.append(current_chunk.strip())
                    current_chunk = paragraph + "\n\n"

            if current_chunk.strip():
                chunks.append(current_chunk.strip())
        else:
            chunks = [text]

        print(f"文本分块: {len(chunks)} 个chunks, 总长度: {len(text)} 字符")

        # 合并所有chunk的分析结果
        merged_result = {
            "vocabulary": {},
            "sentence_structure": {},
            "stylistic_features": {},
        }

        # 逐个处理chunk
        for i, chunk in enumerate(chunks):
            try:
                print(f"处理chunk {i + 1}/{len(chunks)}, 长度: {len(chunk)} 字符")

                # 使用spacy分析
                doc = self.nlp(chunk)

                # 分析这个chunk
                chunk_result = self._analyze_chunk(doc, section)

                # 合并结果
                self._merge_chunk_results(merged_result, chunk_result)

                # 清理内存
                del doc

                # 强制垃圾回收
                import gc

                gc.collect()

            except Exception as e:
                print(f"处理chunk {i + 1}时出错: {e}")
                # 如果单个chunk失败，尝试更小的分块
                if len(chunk) > 10000:
                    print("尝试更小的分块...")
                    smaller_chunks = self._create_smaller_chunks(chunk, 5000)
                    for smaller_chunk in smaller_chunks:
                        try:
                            doc = self.nlp(smaller_chunk)
                            chunk_result = self._analyze_chunk(doc, section)
                            self._merge_chunk_results(merged_result, chunk_result)
                            del doc
                        except Exception as e2:
                            print(f"小chunk处理也失败: {e2}")
                            continue
                continue

        return merged_result

        # 词频统计
        nouns = [
            token.text.lower()
            for token in doc
            if token.pos_ == "NOUN"
            and token.text.lower() not in self.stop_words
            and len(token.text) > 2
        ]
        verbs = [
            token.lemma_.lower()
            for token in doc
            if token.pos_ == "VERB"
            and token.text.lower() not in self.stop_words
            and len(token.text) > 2
        ]
        adjectives = [
            token.text.lower()
            for token in doc
            if token.pos_ == "ADJ"
            and token.text.lower() not in self.stop_words
            and len(token.text) > 2
        ]
        adverbs = [
            token.text.lower()
            for token in doc
            if token.pos_ == "ADV"
            and token.text.lower() not in self.stop_words
            and len(token.text) > 2
        ]

        # 时态分析
        tense_counts = {"past": 0, "present": 0, "future": 0}
        for token in doc:
            if token.tag_ == "VBD" or (token.tag_ == "VBN" and not token.dep_ == "aux"):
                tense_counts["past"] += 1
            elif token.tag_.startswith("VB"):
                tense_counts["present"] += 1

        total_verbs = sum(tense_counts.values())
        if total_verbs > 0:
            tense_pct = {k: round(v / total_verbs, 2) for k, v in tense_counts.items()}
        else:
            tense_pct = {"past": 0, "present": 0, "future": 0}

        # 句子分析
        sentences = list(sent_tokenize(text))
        sentence_lengths = [len(sent.split()) for sent in sentences]

        avg_length = (
            sum(sentence_lengths) / len(sentence_lengths) if sentence_lengths else 0
        )

        # 过渡词统计
        text_lower = text.lower()
        transition_counts = defaultdict(int)
        for category, words in self.TRANSITION_CATEGORIES.items():
            for word in words:
                count = len(re.findall(r"\b" + word + r"\b", text_lower))
                if count > 0:
                    transition_counts[category] += count

        # 连词统计
        conjunction_counts = defaultdict(int)
        conjunction_counts["coordinating"] = sum(
            1 for token in doc if token.lower_ in self.COORDINATING_CONJUNCTIONS
        )
        conjunction_counts["subordinating"] = sum(
            1 for token in doc if token.lower_ in self.SUBORDINATING_CONJUNCTIONS
        )

        # 介词统计
        prepositions = [
            token.text.lower()
            for token in doc
            if token.pos_ == "ADP" and len(token.text) > 1
        ]

        # 被动语态检测
        passive_count = sum(1 for token in doc if token.dep_ == "nsubjpass")
        total_clauses = len(list(doc.sents))
        passive_ratio = passive_count / total_clauses if total_clauses > 0 else 0

        # 句子结构分析
        sentences = list(sent_tokenize(text))
        sentence_lengths = [len(sent.split()) for sent in sentences]

        # 长短句分布
        short_sentences = sum(
            1 for length in sentence_lengths if length <= 10
        )  # 短句：≤10词
        medium_sentences = sum(
            1 for length in sentence_lengths if 11 <= length <= 25
        )  # 中句：11-25词
        long_sentences = sum(
            1 for length in sentence_lengths if length > 25
        )  # 长句：>25词

        total_sentences = len(sentences)
        length_distribution = {
            "short": short_sentences / total_sentences if total_sentences > 0 else 0,
            "medium": medium_sentences / total_sentences if total_sentences > 0 else 0,
            "long": long_sentences / total_sentences if total_sentences > 0 else 0,
        }

        # 句型分析（简单版本）
        simple_sentences = 0
        compound_sentences = 0
        complex_sentences = 0

        for sent in sentences:
            sent_doc = self.nlp(sent)
            coordinating_conj = sum(
                1
                for token in sent_doc
                if token.lower_ in self.COORDINATING_CONJUNCTIONS
            )
            subordinating_conj = sum(
                1
                for token in sent_doc
                if token.lower_ in self.SUBORDINATING_CONJUNCTIONS
            )

            if subordinating_conj > 0:
                complex_sentences += 1
            elif coordinating_conj > 0:
                compound_sentences += 1
            else:
                simple_sentences += 1

        sentence_types = {
            "simple": simple_sentences / total_sentences if total_sentences > 0 else 0,
            "compound": compound_sentences / total_sentences
            if total_sentences > 0
            else 0,
            "complex": complex_sentences / total_sentences
            if total_sentences > 0
            else 0,
        }

        return {
            "nouns": Counter(nouns),
            "verbs": Counter(verbs),
            "adjectives": Counter(adjectives),
            "adverbs": Counter(adverbs),
            "prepositions": Counter(prepositions),
            "tense_distribution": tense_pct,
            "avg_sentence_length": round(avg_length, 2),
            "transition_counts": dict(transition_counts),
            "conjunction_counts": dict(conjunction_counts),
            "passive_ratio": round(passive_ratio, 2),
            "sentence_length_distribution": length_distribution,
            "sentence_types": sentence_types,
        }

    def _analyze_chunk(self, doc, section: str) -> Dict:
        """分析单个文档chunk"""
        try:
            # 词频统计
            nouns = [
                token.text.lower()
                for token in doc
                if token.pos_ == "NOUN"
                and token.text.lower() not in self.stop_words
                and len(token.text) > 2
            ]
            verbs = [
                token.lemma_.lower()
                for token in doc
                if token.pos_ == "VERB"
                and token.text.lower() not in self.stop_words
                and len(token.text) > 2
            ]
            adjectives = [
                token.text.lower()
                for token in doc
                if token.pos_ == "ADJ"
                and token.text.lower() not in self.stop_words
                and len(token.text) > 2
            ]
            adverbs = [
                token.text.lower()
                for token in doc
                if token.pos_ == "ADV"
                and token.text.lower() not in self.stop_words
                and len(token.text) > 2
            ]

            # 计算词频
            from collections import Counter

            noun_freq = Counter(nouns)
            verb_freq = Counter(verbs)
            adj_freq = Counter(adjectives)
            adv_freq = Counter(adverbs)

            # 句子长度统计
            sentence_lengths = [len(sent.text.split()) for sent in doc.sents]
            avg_sentence_length = (
                sum(sentence_lengths) / len(sentence_lengths) if sentence_lengths else 0
            )

            # 被动语态检测
            passive_count = sum(1 for token in doc if token.dep_ == "nsubjpass")
            passive_ratio = (
                passive_count / len(list(doc.sents)) if list(doc.sents) else 0
            )

            return {
                "vocabulary": {
                    "nouns": dict(noun_freq.most_common(20)),
                    "verbs": dict(verb_freq.most_common(20)),
                    "adjectives": dict(adj_freq.most_common(20)),
                    "adverbs": dict(adv_freq.most_common(20)),
                },
                "sentence_structure": {
                    "avg_sentence_length": avg_sentence_length,
                    "sentence_count": len(list(doc.sents)),
                    "total_tokens": len(doc),
                },
                "stylistic_features": {
                    "passive_voice_ratio": passive_ratio,
                    "token_count": len(doc),
                },
            }
        except Exception as e:
            print(f"chunk分析失败: {e}")
            return {
                "vocabulary": {
                    "nouns": {},
                    "verbs": {},
                    "adjectives": {},
                    "adverbs": {},
                },
                "sentence_structure": {
                    "avg_sentence_length": 0,
                    "sentence_count": 0,
                    "total_tokens": 0,
                },
                "stylistic_features": {"passive_voice_ratio": 0, "token_count": 0},
            }

    def _merge_chunk_results(self, merged: Dict, chunk_result: Dict):
        """合并chunk分析结果"""
        try:
            # 合并词汇频率
            for category in ["nouns", "verbs", "adjectives", "adverbs"]:
                if category in chunk_result.get("vocabulary", {}):
                    for word, freq in chunk_result["vocabulary"][category].items():
                        if category not in merged["vocabulary"]:
                            merged["vocabulary"][category] = {}
                        merged["vocabulary"][category][word] = (
                            merged["vocabulary"][category].get(word, 0) + freq
                        )

            # 合并句子结构（取平均值）
            if "sentence_structure" in chunk_result:
                for key, value in chunk_result["sentence_structure"].items():
                    if key not in merged["sentence_structure"]:
                        merged["sentence_structure"][key] = []
                    merged["sentence_structure"][key].append(value)

            # 确保返回正确的数据结构，兼容传统分析器期望的格式
            if "vocabulary" in merged:
                # 转换为传统格式
                merged["nouns"] = merged["vocabulary"].get("nouns", {})
                merged["verbs"] = merged["vocabulary"].get("verbs", {})
                merged["adjectives"] = merged["vocabulary"].get("adjectives", {})
                merged["adverbs"] = merged["vocabulary"].get("adverbs", {})

                # 计算平均值用于句子结构
                if "avg_sentence_length" in merged["sentence_structure"]:
                    lengths = merged["sentence_structure"]["avg_sentence_length"]
                    if lengths and isinstance(lengths, list):
                        merged["avg_sentence_length"] = sum(lengths) / len(lengths)
                    elif isinstance(lengths, (int, float)):
                        merged["avg_sentence_length"] = lengths

                if "passive_voice_ratio" in merged["stylistic_features"]:
                    ratios = merged["stylistic_features"]["passive_voice_ratio"]
                    if ratios and isinstance(ratios, list):
                        merged["passive_voice_ratio"] = sum(ratios) / len(ratios)
                    elif isinstance(ratios, (int, float)):
                        merged["passive_voice_ratio"] = ratios

            # 合并文体特征
            if "stylistic_features" in chunk_result:
                for key, value in chunk_result["stylistic_features"].items():
                    if key not in merged["stylistic_features"]:
                        merged["stylistic_features"][key] = []
                    merged["stylistic_features"][key].append(value)

        except Exception as e:
            print(f"合并结果时出错: {e}")

    def _create_smaller_chunks(self, text: str, chunk_size: int) -> List[str]:
        """创建更小的文本chunks"""
        chunks = []
        words = text.split()

        for i in range(0, len(words), chunk_size):
            chunk_words = words[i : i + chunk_size]
            chunk = " ".join(chunk_words)
            if chunk.strip():
                chunks.append(chunk)

        return chunks

    def analyze_papers(
        self, paper_paths: List[Path], journal_name: str = "Target Journal"
    ) -> JournalStyleReport:
        """
        分析多篇论文

        Args:
            paper_paths: PDF文件路径列表
            journal_name: 期刊名称

        Returns:
            完整的风格分析报告
        """
        from datetime import datetime

        report = JournalStyleReport()
        report.journal_name = journal_name
        report.analysis_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        report.papers_analyzed = len(paper_paths)

        # 聚合所有分析结果
        all_nouns = Counter()
        all_verbs = Counter()
        all_adjectives = Counter()
        all_adverbs = Counter()
        all_prepositions = Counter()
        all_hedging = Counter()
        all_tense = defaultdict(list)
        all_transitions = defaultdict(list)
        all_conjunctions = defaultdict(list)
        all_sentence_lengths = []
        all_sentence_length_distributions = defaultdict(list)
        all_sentence_types = defaultdict(list)
        passive_ratios = []

        for paper_path in paper_paths:
            sections = self.extract_text_from_pdf(paper_path)

            for section, text in sections.items():
                if not text.strip():
                    continue

                analysis = self.analyze_text(text, section)

                # 聚合词汇
                all_nouns.update(analysis.get("nouns", {}))
                all_verbs.update(analysis.get("verbs", {}))
                all_adjectives.update(analysis.get("adjectives", {}))
                all_adverbs.update(analysis.get("adverbs", {}))
                all_prepositions.update(analysis.get("prepositions", {}))

                # Hedging词汇
                for word in self.HEDGING_TERMS:
                    count = text.lower().count(word)
                    if count > 0:
                        all_hedging[word] += count

                # 时态分布
                tense = analysis.get("tense_distribution", {})
                if tense:
                    section_key = section if section != "general" else "general"
                    all_tense[section_key].append(tense)

                # 过渡词
                transitions = analysis.get("transition_counts", {})
                for cat, count in transitions.items():
                    all_transitions[cat] = all_transitions.get(cat, 0) + count

                # 连词
                conjunctions = analysis.get("conjunction_counts", {})
                for cat, count in conjunctions.items():
                    all_conjunctions[cat] = all_conjunctions.get(cat, 0) + count

                # 句子长度
                all_sentence_lengths.append(analysis.get("avg_sentence_length", 0))

                # 句子长度分布
                length_dist = analysis.get("sentence_length_distribution", {})
                for dist_type, ratio in length_dist.items():
                    all_sentence_length_distributions[dist_type].append(ratio)

                # 句型分布
                sentence_types = analysis.get("sentence_types", {})
                for sent_type, ratio in sentence_types.items():
                    all_sentence_types[sent_type].append(ratio)

                # 被动语态
                passive_ratios.append(analysis.get("passive_ratio", 0))

        # 计算平均值
        report.high_frequency_nouns = all_nouns.most_common(50)
        report.high_frequency_verbs = all_verbs.most_common(30)
        report.high_frequency_adjectives = all_adjectives.most_common(40)
        report.high_frequency_adverbs = all_adverbs.most_common(40)
        report.prepositions = all_prepositions.most_common(40)
        report.hedging_terms = all_hedging.most_common(20)

        # 时态分布（按章节平均）
        for section, pcts in all_tense.items():
            if pcts:
                avg_pcts = {
                    "past": round(sum(p["past"] for p in pcts) / len(pcts), 2),
                    "present": round(sum(p["present"] for p in pcts) / len(pcts), 2),
                    "future": round(sum(p["future"] for p in pcts) / len(pcts), 2),
                }
                report.tense_distribution[section] = avg_pcts

        # 过渡词
        for cat, count in all_transitions.items():
            report.transition_words[cat] = [(cat, count)]

        # 连词
        for cat, count in all_conjunctions.items():
            report.conjunctions[cat] = [(cat, count)]

        # 句子结构
        avg_length = (
            sum(all_sentence_lengths) / len(all_sentence_lengths)
            if all_sentence_lengths
            else 0
        )
        avg_passive = sum(passive_ratios) / len(passive_ratios) if passive_ratios else 0

        # 句子长度分布平均值
        sentence_length_dist_avg = {}
        for dist_type in ["short", "medium", "long"]:
            if dist_type in all_sentence_length_distributions:
                ratios = all_sentence_length_distributions[dist_type]
                sentence_length_dist_avg[dist_type] = (
                    round(sum(ratios) / len(ratios), 3) if ratios else 0
                )

        # 句型分布平均值
        sentence_types_avg = {}
        for sent_type in ["simple", "compound", "complex"]:
            if sent_type in all_sentence_types:
                ratios = all_sentence_types[sent_type]
                sentence_types_avg[sent_type] = (
                    round(sum(ratios) / len(ratios), 3) if ratios else 0
                )

        report.sentence_structure = {
            "average_sentence_length": round(avg_length, 2),
            "passive_voice_ratio": round(avg_passive, 2),
            "papers_analyzed": len(paper_paths),
        }

        report.sentence_length_distribution = sentence_length_dist_avg
        report.sentence_types = sentence_types_avg

        return report

    def generate_writing_guides(self, report: JournalStyleReport) -> Dict[str, str]:
        """
        根据分析报告生成写作指南 - 支持传统分析和AI增强8维度分析
        """
        guides = {}

        # 检查是否有AI增强的8维度分析结果
        if hasattr(report, "section_style_cards") and report.section_style_cards:
            print("使用AI增强的8维度分析结果生成指南")
            return self._generate_ai_style_guides(report)
        else:
            print("使用传统分析生成指南")
            return self._generate_traditional_guides(report)

    def _generate_ai_style_guides(self, report: JournalStyleReport) -> Dict[str, str]:
        """基于AI增强的8维度分析生成写作指南"""
        guides = {}

        for section_name, style_card in report.section_style_cards.items():
            # 使用我们之前修复的generate_section_guide函数
            from .ai_deepseek_analyzer import generate_section_guide

            guide_content = generate_section_guide(style_card)
            guides[section_name] = guide_content

            print(f"生成{section_name}的8维度指南，长度: {len(guide_content)} 字符")

        return guides

    def _generate_traditional_guides(
        self, report: JournalStyleReport
    ) -> Dict[str, str]:
        """基于传统分析生成写作指南（原有逻辑）"""
        guides = {}

        # 提取关键特征
        nouns = [n for n, _ in report.high_frequency_nouns[:20]]
        verbs = [v for v, _ in report.high_frequency_verbs[:15]]
        adjectives = [adj for adj, _ in report.high_frequency_adjectives[:15]]
        adverbs = [adv for adv, _ in report.high_frequency_adverbs[:15]]
        prepositions = [prep for prep, _ in report.prepositions[:15]]
        tense = report.tense_distribution
        transitions = report.transition_words
        conjunctions = report.conjunctions
        passive_ratio = report.sentence_structure.get("passive_voice_ratio", 0.5)
        sentence_length_dist = report.sentence_length_distribution
        sentence_types = report.sentence_types

        # 摘要写作指南
        abstract_guide = f"""# Abstract Writing Guide for {report.journal_name}

## Tense Usage
- Background: Present tense (约{tense.get("abstract", {}).get("present", 80)}%)
- Methods: Past tense (约{tense.get("abstract", {}).get("past", 20)}%)
- Results: Present tense
- Conclusions: Present tense

## Structure
1. Background/Purpose (1-2 sentences)
2. Methods (1 sentence)
3. Results (2-3 sentences, include key findings and statistics)
4. Conclusions (1-2 sentences, clinical/research implications)

## Key Vocabulary (Top 40)
### Nouns: {", ".join(nouns[:20])}
### Verbs: {", ".join(verbs[:10])}
### Adjectives: {", ".join(adjectives[:10])}

## Sentence Structure
- Average length: {report.sentence_structure.get("average_sentence_length", 22)} words
- Sentence types: Simple {sentence_types.get("simple", 0.4) * 100:.0f}%, Compound {sentence_types.get("compound", 0.3) * 100:.0f}%, Complex {sentence_types.get("complex", 0.3) * 100:.0f}%
- Length distribution: Short {sentence_length_dist.get("short", 0.3) * 100:.0f}%, Medium {sentence_length_dist.get("medium", 0.5) * 100:.0f}%, Long {sentence_length_dist.get("long", 0.2) * 100:.0f}%

## Style Notes
- Length: 150-250 words (check journal requirements)
- No citations or abbreviations (unless defined)
- Write in complete sentences, avoid bullet points
- Passive voice ratio: {passive_ratio * 100:.0f}%
- Focus on most important findings first
- Use coordinating conjunctions sparingly, prefer complex sentences
"""
        guides["abstract"] = abstract_guide

        # 引言写作指南
        intro_guide = f"""# Introduction Writing Guide for {report.journal_name}

## Tense Usage
- Background information: Present tense (约{tense.get("introduction", {}).get("present", 70)}%)
- Previous studies: Past tense (约{tense.get("introduction", {}).get("past", 30)}%)
- Research gap: Present tense

## Key Vocabulary (Top 40)
### Nouns: {", ".join(nouns[:15])}
### Verbs: {", ".join(verbs[:12])}
### Adjectives: {", ".join(adjectives[:8])}
### Adverbs: {", ".join(adverbs[:5])}

## Transition Words
Sequential: {", ".join([t for t, _ in transitions.get("sequential", [])[:8]])}
Contrastive: {", ".join([t for t, _ in transitions.get("contrastive", [])[:6]])}
Causal: {", ".join([t for t, _ in transitions.get("causal", [])[:4]])}

## Conjunctions
Coordinating: and, but, or, nor, for, so, yet (use {conjunctions.get("coordinating", [(0, 0)])[0][1] if conjunctions.get("coordinating") else 0} per 1000 words)
Subordinating: although, because, while, since, if, when (use {conjunctions.get("subordinating", [(0, 0)])[0][1] if conjunctions.get("subordinating") else 0} per 1000 words)

## Sentence Structure
- Average length: {report.sentence_structure.get("average_sentence_length", 22)} words
- Sentence types: Simple {sentence_types.get("simple", 0.35) * 100:.0f}%, Compound {sentence_types.get("compound", 0.35) * 100:.0f}%, Complex {sentence_types.get("complex", 0.3) * 100:.0f}%
- Length distribution: Short {sentence_length_dist.get("short", 0.25) * 100:.0f}%, Medium {sentence_length_dist.get("medium", 0.55) * 100:.0f}%, Long {sentence_length_dist.get("long", 0.2) * 100:.0f}%

## Prepositions (Top 15)
{", ".join(prepositions[:15])}

## Structure
1. Broad context (2-3 sentences)
2. Specific problem (2-3 sentences)
3. Literature summary (3-4 sentences)
4. Research gap (1-2 sentences)
5. Study objectives (1-2 sentences)

## Style Notes
- Passive voice ratio: {passive_ratio * 100:.0f}%
- Use complex sentences for literature discussion
- Employ hedging terms appropriately: {", ".join([h for h, _ in report.hedging_terms[:8]])}
- Transition smoothly between ideas using contrastive words
"""
        guides["introduction"] = intro_guide

        # 方法写作指南
        methods_guide = f"""# Methods Writing Guide for {report.journal_name}

## Tense Usage
- Procedures: Past tense (>95%)
- Definitions: Present tense (<5%)

## Key Vocabulary (Top 40)
### Nouns: {", ".join(nouns[:15])}
### Verbs: {", ".join(verbs[:12])}
### Adjectives: {", ".join(adjectives[:8])}
### Adverbs: {", ".join(adverbs[:5])}

## Prepositions (Technical)
{", ".join(prepositions[:12])}

## Sentence Structure
- Average length: {report.sentence_structure.get("average_sentence_length", 20)} words
- Prefer longer, detailed sentences for procedures
- Sentence types: Simple {sentence_types.get("simple", 0.2) * 100:.0f}%, Compound {sentence_types.get("compound", 0.4) * 100:.0f}%, Complex {sentence_types.get("complex", 0.4) * 100:.0f}%
- Length distribution: Short {sentence_length_dist.get("short", 0.15) * 100:.0f}%, Medium {sentence_length_dist.get("medium", 0.6) * 100:.0f}%, Long {sentence_length_dist.get("long", 0.25) * 100:.0f}%

## Transition Words
Sequential: {", ".join([t for t, _ in transitions.get("sequential", [])[:6]])}
Causal: {", ".join([t for t, _ in transitions.get("causal", [])[:4]])}

## Conjunctions
Coordinating: and, or (technical coordination)
Subordinating: if, when, although (conditional procedures)

## Structure
1. Study design overview
2. Participants/materials description
3. Experimental procedures
4. Statistical analysis
5. Ethical statements

## Style Notes
- Passive voice ratio: {passive_ratio * 100:.0f}% (high for objectivity)
- Detailed enough for reproducibility
- Include sample size calculations if applicable
- Use precise technical vocabulary
- Avoid vague terms: {", ".join([h for h, _ in report.hedging_terms[:5]])}
"""
        guides["methods"] = methods_guide

        # 结果写作指南
        results_guide = f"""# Results Writing Guide for {report.journal_name}

## Tense Usage
- Findings: Past tense (约{tense.get("results", {}).get("past", 85)}%)
- Figure/table references: Present tense

## Structure
1. Primary outcomes (first)
2. Secondary outcomes
3. Secondary analyses

## Style Notes
- Objective reporting without interpretation
- Report statistics with exact values
- Reference figures/tables: "As shown in Figure 1..."
- Passive voice ratio: {passive_ratio * 100:.0f}%

## Common Phrases
- "The results indicated that..."
- "A significant difference was observed..."
- "Data analysis revealed..."
"""
        guides["results"] = results_guide

        # 讨论写作指南
        discussion_guide = f"""# Discussion Writing Guide for {report.journal_name}

## Tense Usage
- Interpretations: Present tense (约{tense.get("discussion", {}).get("present", 75)}%)
- Study findings: Past tense

## Structure
1. Principal findings summary (2-3 sentences)
2. Interpretation and comparison with literature (3-5 sentences)
3. Implications (2-3 sentences)
4. Limitations (2-3 sentences)
5. Future directions (1-2 sentences)

## Style Notes
- Balance confidence and caution
- Use hedging terms appropriately

## Common Phrases
- "These findings suggest that..."
- "In contrast to previous studies..."
- "The implications of these results are..."
- "One limitation of this study is..."
- "Future research should investigate..."
"""
        guides["discussion"] = discussion_guide

        # 结论写作指南
        conclusion_guide = f"""# Conclusion Writing Guide for {report.journal_name}

## Tense Usage
- Summary statements: Present tense (约{tense.get("conclusion", {}).get("present", 90)}%)
- Key findings: Present perfect or present tense
- Future implications: Present tense

## Structure
1. Restate main findings (2-3 sentences)
2. Emphasize significance/contribution (1-2 sentences)
3. Practical/theoretical implications (1-2 sentences)
4. Final concluding statement (1 sentence)

## Key Vocabulary
{", ".join(nouns[:12])}
{", ".join(verbs[:8])}

## Style Notes
- Concise and focused (typically 150-300 words)
- Avoid introducing new information
- Strong, confident language
- Connect back to original research question/hypothesis
- Passive voice ratio: {passive_ratio * 100:.0f}%

## Common Phrases
- "In conclusion, these findings demonstrate that..."
- "The present study provides evidence that..."
- "These results contribute to our understanding of..."
- "The implications of this research are..."
- "Further investigation is warranted to..."
"""
        guides["conclusion"] = conclusion_guide

        return guides

    def save_report_and_guides(
        self, report: JournalStyleReport, output_dir: str
    ) -> Dict[str, str]:
        """
        保存报告和写作指南

        Args:
            report: 风格分析报告
            output_dir: 输出目录

        Returns:
            输出文件路径字典
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # 保存报告
        report_path = output_path / "journal_style_report.json"
        report.save(str(report_path))

        # 生成并保存写作指南
        guides = self.generate_writing_guides(report)
        guide_paths = {}

        for section, guide_content in guides.items():
            guide_path = output_path / f"{section}_guide.md"
            with open(guide_path, "w", encoding="utf-8") as f:
                f.write(guide_content)
            guide_paths[section] = str(guide_path)

        # 保存风格摘要
        summary_path = output_path / "style_summary.md"
        with open(summary_path, "w", encoding="utf-8") as f:
            f.write(f"# {report.journal_name} Style Summary\n\n")
            f.write(f"Analyzed {report.papers_analyzed} papers\n\n")
            f.write("## Key Vocabulary\n")
            f.write(
                "- Top nouns: {}\n".format(
                    ", ".join([n for n, _ in report.high_frequency_nouns[:10]])
                )
            )
            f.write(
                "- Top verbs: {}\n".format(
                    ", ".join([v for v, _ in report.high_frequency_verbs[:10]])
                )
            )
            f.write("\n## Tense Distribution\n")
            for section, dist in report.tense_distribution.items():
                f.write(
                    f"- {section}: Present {dist.get('present', 0) * 100:.0f}%, Past {dist.get('past', 0) * 100:.0f}%\n"
                )
            f.write("\n## Style Metrics\n")
            f.write(
                f"- Average sentence length: {report.sentence_structure.get('average_sentence_length', 20)} words\n"
            )
            f.write(
                f"- Passive voice ratio: {report.sentence_structure.get('passive_voice_ratio', 0.5) * 100:.0f}%\n"
            )

        return {
            "report": str(report_path),
            "guides": guide_paths,
            "summary": str(summary_path),
        }


def analyze_journal_style(
    papers_dir: str, output_dir: str, journal_name: str = "Target Journal"
) -> Dict[str, str]:
    """
    分析期刊风格的便捷函数

    Args:
        papers_dir: 包含PDF论文的目录
        output_dir: 输出目录
        journal_name: 期刊名称

    Returns:
        输出文件路径字典
    """
    paper_dir = Path(papers_dir)
    paper_paths = (
        list(paper_dir.glob("*.pdf"))
        + list(paper_dir.glob("*.txt"))
        + list(paper_dir.glob("*.md"))
    )

    if not paper_paths:
        raise ValueError(f"在 {papers_dir} 中未找到PDF/TXT/MD文件")

    analyzer = JournalStyleAnalyzer()
    report = analyzer.analyze_papers(paper_paths, journal_name)

    return analyzer.save_report_and_guides(report, output_dir)


if __name__ == "__main__":
    import sys

    if len(sys.argv) >= 3:
        papers_dir = sys.argv[1]
        output_dir = sys.argv[2]
        journal_name = sys.argv[3] if len(sys.argv) > 3 else "Target Journal"

        result = analyze_journal_style(papers_dir, output_dir, journal_name)
        print(f"分析完成！")
        print(f"报告: {result['report']}")
        print(f"引言指南: {result['guides'].get('introduction', 'N/A')}")
        print(f"方法指南: {result['guides'].get('methods', 'N/A')}")
        print(f"结果指南: {result['guides'].get('results', 'N/A')}")
        print(f"讨论指南: {result['guides'].get('discussion', 'N/A')}")
    else:
        print("用法: python journal_style_analyzer.py <论文目录> <输出目录> [期刊名称]")
