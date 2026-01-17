"""
Multi-Agent Coordinator Module
Supports calling multiple AI providers via API
Supports per-section model configuration for optimal cost-performance ratio
Supports LaTeX output with strict citation requirements
"""

import json
import time
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import requests


# Recommended model configuration for each section (cost-performance optimized)
# Using Claude for critical thinking sections, GPT for structure
SECTION_MODEL_CONFIG = {
    "introduction": {
        "model": "GPT-4o",
        "temperature": 0.7,
        "description": "Deep academic analysis, citation synthesis",
    },
    "methods": {
        "model": "GPT-4o",
        "temperature": 0.7,
        "description": "Precise structured description",
    },
    "results": {
        "model": "GPT-4o",
        "temperature": 0.7,
        "description": "Accurate data presentation",
    },
    "discussion": {
        "model": "Claude-Sonnet-4.5",
        "temperature": 0.7,
        "description": "Critical thinking, interpretation, comparison",
    },
    "abstract": {
        "model": "GPT-4o",
        "temperature": 0.5,
        "description": "Concise global summary",
    },
    "conclusion": {
        "model": "Claude-Sonnet-4.5",
        "temperature": 0.7,
        "description": "Refined summary, forward thinking",
    },
}

# Default global model fallback
DEFAULT_MODEL = "gpt-4o"


class AgentStatus(Enum):
    """Agent status"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    APPROVED = "approved"
    REJECTED = "rejected"
    COMPLETED = "completed"


@dataclass
class Task:
    """Task"""

    id: str
    agent_type: str
    status: AgentStatus = AgentStatus.PENDING
    input_data: Dict[str, Any] = field(default_factory=dict)
    output_data: Optional[str] = None
    quality_score: float = 0.0
    error_message: Optional[str] = None
    retry_count: int = 0
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: Optional[str] = None
    duration_seconds: float = 0.0


@dataclass
class SectionResult:
    """Section result"""

    section_name: str
    content: str
    word_count: int
    citations_used: List[str]
    quality_score: float
    status: AgentStatus


class APIClient:
    """API client for calling AI models"""

    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

    def call_model(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4000,
    ) -> str:
        """Call AI model with messages"""
        url = f"{self.base_url}/chat/completions"

        data = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        try:
            response = requests.post(url, json=data, headers=self.headers, timeout=120)
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"]
        except requests.exceptions.RequestException as e:
            raise Exception(f"API调用失败: {str(e)}")


class SkillGeneratorAgent(BaseAgent):
    """一级AI：生成详细的写作skill指导"""

    def __init__(self, api_client: APIClient, model: str = "claude-sonnet-4-20250514"):
        super().__init__("SkillGeneratorAgent", api_client, model)

    def generate_skill(
        self,
        section_name: str,
        context: Dict[str, Any],
        style_guide: str,
        research_content: str,
    ) -> Dict[str, Any]:
        """生成章节写作skill

        Args:
            section_name: 章节名称
            context: 写作上下文
            style_guide: 风格指南
            research_content: 用户研究内容

        Returns:
            skill字典，包含分段、架构等详细指导
        """

        prompt = f"""你是一级AI写作指导专家，专门为学术论文各章节生成详细的写作skill。

## 任务要求
基于以下信息，为"{section_name}"章节生成详细的写作skill：

## 输入信息
### 1. 章节类型：{section_name}
### 2. 目标期刊风格指南：
{style_guide}

### 3. 用户研究内容：
{research_content}

### 4. 写作目标：
为二级AI提供完整的写作指导，包括结构、内容要点、写作思路等。

## 重要提醒
生成skill时，必须在"execution_instructions"字段中明确指示二级AI：
同时参照此skill文件和对应的章节风格提取文件进行写作。

## Skill输出格式（严格遵循）

请以JSON格式输出，包含以下字段：

```json
{{
  "section_name": "{section_name}",
  "overall_structure": {{
    "paragraph_count": "建议的段落数量",
    "main_sections": ["主要部分1", "主要部分2", ...],
    "transition_strategy": "段落间过渡策略"
  }},
  "paragraph_details": [
    {{
      "paragraph_id": 1,
      "title": "段落标题",
      "purpose": "段落目的",
      "content_outline": ["要点1", "要点2", ...],
      "writing_approach": "写作思路和方法",
      "citation_strategy": "引用策略",
      "word_count_estimate": "字数估算"
    }},
    {{
      "paragraph_id": 2,
      ...
    }}
  ],
  "key_messages": ["核心信息点1", "核心信息点2", ...],
  "rhetorical_strategy": "修辞策略",
  "citation_requirements": {{
    "frequency": "引用频率",
    "types": ["引用类型"],
    "relevance_criteria": "相关性标准"
  }},
  "execution_instructions": [
    "同时参照此skill文件和对应的{section_name}章节风格提取文件进行写作",
    "skill文件提供具体写作结构和要点",
    "风格提取文件提供写作风格、语言特点和表达偏好",
    "将两种指导有机结合，确保内容和风格的双重符合",
    "优先遵循skill的结构要求，在此基础上应用风格指南的语言规范"
  ],
  "quality_checkpoints": ["质量检查点1", "质量检查点2", ...],
  "common_pitfalls": ["常见错误1", "常见错误2", ...]
}}
```

## 要求
- 详细分析用户研究内容，提取相关要点
- 结合期刊风格指南，提供具体写作指导
- 确保结构合理，逻辑清晰
- 提供可操作的写作步骤
- 必须包含execution_instructions，明确要求参照两个文件

输出纯JSON，不要其他内容。"""

        response = self._call_ai(prompt, temperature=0.3)  # 低温度确保一致性

        try:
            # 清理响应，只保留JSON部分
            json_start = response.find("{")
            json_end = response.rfind("}") + 1
            if json_start != -1 and json_end > json_start:
                json_content = response[json_start:json_end]
                skill = json.loads(json_content)
                return skill
        except Exception as e:
            print(f"解析skill JSON失败: {e}")
            return self._generate_default_skill(section_name, context)


class BaseAgent:
    """Base class for all writing agents with LaTeX output support"""

    def __init__(self, name: str, api_client: APIClient, model: str = "gpt-4o"):
        self.name = name
        self.api_client = api_client
        self.model = model

    def write_section(
        self, context: Dict[str, Any], requirements: Dict[str, Any]
    ) -> str:
        """传统写作方法（兼容旧代码）"""
        return self.write_section_with_skill(context, {})

    def write_section_with_skill(
        self, context: Dict[str, Any], skill: Dict[str, Any]
    ) -> str:
        """根据skill进行写作（新方法）

        Args:
            context: 写作上下文
            skill: 一级AI生成的写作skill

        Returns:
            生成的章节内容
        """
        raise NotImplementedError

    def search_relevant_literature(
        self,
        section_name: str,
        skill: Dict[str, Any],
        literature_db: Any,
        query_limit: int = 3,
    ) -> Dict[str, List[Any]]:
        """根据skill为每个句子搜索最相关的1-3篇文献

        优先选择：
        1. 经典论文（高引用次数）
        2. 最新论文（最近发表）
        3. 权威期刊论文

        Args:
            section_name: 章节名称
            skill: 写作skill
            literature_db: 文献数据库管理器
            query_limit: 每个句子的搜索结果限制（1-3篇）

        Returns:
            字典：句子ID -> 相关文献列表
        """
        sentence_literature = {}

        # 为每个段落的每个句子搜索文献
        paragraph_details = skill.get("paragraph_details", [])

        for para in paragraph_details:
            para_id = para.get("paragraph_id")
            content_outline = para.get("content_outline", [])
            para_title = para.get("title", "")

            # 为段落标题生成句子
            title_sentences = [f"Paragraph title: {para_title}"]

            # 从内容要点生成句子
            content_sentences = []
            for outline_point in content_outline:
                # 将内容要点拆分为句子
                sentences = re.split(r"[.!?]+", outline_point.strip())
                content_sentences.extend([s.strip() for s in sentences if s.strip()])

            # 合并所有句子
            all_sentences = title_sentences + content_sentences

            # 为每个句子搜索文献
            for sent_idx, sentence in enumerate(all_sentences):
                sentence_keywords = self._extract_sentence_keywords(sentence)

                if sentence_keywords and literature_db:
                    search_query = " ".join(sentence_keywords)
                    try:
                        # 搜索更多结果，然后按质量排序选择最好的1-3篇
                        all_candidates = literature_db.search_with_citekeys(
                            query=search_query,
                            limit=10,  # 搜索10个候选，然后筛选
                        )

                        # 按质量排序并选择前1-3篇
                        top_papers = self._rank_and_select_papers(
                            all_candidates, query_limit
                        )

                        sentence_key = f"para_{para_id}_sent_{sent_idx}"
                        sentence_literature[sentence_key] = top_papers

                    except Exception as e:
                        print(f"句子 '{sentence[:50]}...' 文献搜索失败: {e}")
                        continue

        # 提供章节级别的补充文献
        chapter_keywords = []
        key_messages = skill.get("key_messages", [])
        for msg in key_messages[:2]:
            words = re.findall(r"\b[a-zA-Z]{4,}\b", msg.lower())
            chapter_keywords.extend(words)

        if chapter_keywords and literature_db:
            unique_keywords = list(set(chapter_keywords))[:3]
            search_query = " ".join(unique_keywords)
            try:
                chapter_candidates = literature_db.search_with_citekeys(
                    query=search_query, limit=15
                )
                chapter_top_papers = self._rank_and_select_papers(chapter_candidates, 8)
                sentence_literature["chapter_supplement"] = chapter_top_papers
            except Exception as e:
                print(f"章节补充文献搜索失败: {e}")
                sentence_literature["chapter_supplement"] = []

        return sentence_literature

    def _extract_sentence_keywords(self, sentence: str) -> List[str]:
        """从句子中提取关键词"""
        # 提取名词性短语和关键词
        words = re.findall(r"\b[a-zA-Z]{4,}\b", sentence.lower())

        # 过滤停用词和常见词
        stop_words = {
            "that",
            "with",
            "have",
            "this",
            "will",
            "from",
            "they",
            "know",
            "want",
            "been",
            "good",
            "much",
            "some",
            "time",
            "very",
            "when",
            "come",
            "here",
            "just",
            "like",
            "long",
            "make",
            "many",
            "over",
            "such",
            "take",
            "than",
            "them",
            "well",
            "were",
        }
        filtered_words = [w for w in words if w not in stop_words and len(w) > 3]

        # 返回前3个最重要的关键词
        return filtered_words[:3]

    def _rank_and_select_papers(self, papers: List[Any], limit: int) -> List[Any]:
        """按质量对论文排序并选择最好的"""
        if not papers:
            return []

        # 为每篇论文计算质量分数
        scored_papers = []
        for paper in papers:
            score = self._calculate_paper_quality_score(paper)
            scored_papers.append((score, paper))

        # 按分数降序排序
        scored_papers.sort(key=lambda x: x[0], reverse=True)

        # 返回前N篇
        return [paper for score, paper in scored_papers[:limit]]

    def _calculate_paper_quality_score(self, paper: Any) -> float:
        """计算论文质量分数

        评分标准：
        - 引用次数 (30%)
        - 发表年份 (25%) - 越新越好
        - 期刊影响力 (25%) - Nature, Science等顶级期刊
        - 标题长度 (10%) - 标题太长可能质量较低
        - 作者数量 (10%) - 适中数量的作者
        """
        score = 0.0

        # 1. 引用次数评分 (0-30分)
        cited_by = getattr(paper, "cited_by", 0) or 0
        if cited_by >= 100:
            citation_score = 30
        elif cited_by >= 50:
            citation_score = 25
        elif cited_by >= 20:
            citation_score = 20
        elif cited_by >= 10:
            citation_score = 15
        elif cited_by >= 5:
            citation_score = 10
        elif cited_by >= 1:
            citation_score = 5
        else:
            citation_score = 0
        score += citation_score

        # 2. 发表年份评分 (0-25分)
        year = getattr(paper, "year", 0) or 0
        current_year = 2024
        if year >= current_year - 2:
            year_score = 25  # 最近2年
        elif year >= current_year - 5:
            year_score = 20  # 最近5年
        elif year >= current_year - 10:
            year_score = 15  # 最近10年
        elif year >= current_year - 20:
            year_score = 10  # 最近20年
        else:
            year_score = 5  # 更早
        score += year_score

        # 3. 期刊影响力评分 (0-25分)
        journal = getattr(paper, "journal", "").lower()
        top_journals = {
            "nature": 25,
            "science": 25,
            "cell": 24,
            "lancet": 24,
            "new england journal of medicine": 24,
            "nature genetics": 23,
            "nature medicine": 23,
            "nature biotechnology": 23,
            "proceedings of the national academy of sciences": 22,
            "jama": 22,
            "nature communications": 20,
            "plos one": 15,
            "scientific reports": 15,
        }

        journal_score = 0
        for top_journal, points in top_journals.items():
            if top_journal in journal:
                journal_score = points
                break

        # 如果不是顶级期刊，但包含某些关键词也给分
        if journal_score == 0:
            if any(word in journal for word in ["nature", "science", "cell", "lancet"]):
                journal_score = 18
            elif any(word in journal for word in ["journal", "review", "proceedings"]):
                journal_score = 12
            else:
                journal_score = 8  # 普通期刊

        score += journal_score

        # 4. 标题长度评分 (0-10分) - 太长可能质量较低
        title = getattr(paper, "title", "")
        title_length = len(title.split())
        if title_length <= 15:
            title_score = 10
        elif title_length <= 20:
            title_score = 8
        elif title_length <= 25:
            title_score = 6
        else:
            title_score = 4
        score += title_score

        # 5. 作者数量评分 (0-10分) - 适中数量的作者
        authors = getattr(paper, "authors", "")
        author_count = len(authors.split(";")) if authors else 1
        if author_count == 1:
            author_score = 8  # 单作者
        elif 2 <= author_count <= 5:
            author_score = 10  # 理想数量
        elif 6 <= author_count <= 10:
            author_score = 8  # 可接受
        elif author_count > 10:
            author_score = 5  # 太多作者
        else:
            author_score = 6
        score += author_score

        return score

    def _build_system_prompt(
        self, chapter_type: str, style_guide: str, context: Dict[str, Any]
    ) -> str:
        """Build system prompt for the agent with LaTeX output requirements"""
        # 获取引用风格配置
        citation_style = context.get("citation_style", {})
        citation_type = citation_style.get("citation_type", "author-year")
        latex_command = citation_style.get("latex_citation_command", "\\citep")

        # 根据章节类型确定引用要求
        citation_requirement = self._get_citation_requirement(chapter_type)

        prompt = f"""You are an academic writing expert specializing in {chapter_type} sections.

## CRITICAL OUTPUT REQUIREMENTS
- **OUTPUT FORMAT: LaTeX** - You MUST output in LaTeX format suitable for academic publication
- **CITATION STYLE**: {citation_type} format using LaTeX commands
- **CITATION COMMAND**: {latex_command}{{citekey}} (e.g., {latex_command}{{Zhang2025}})
- **CITATION RULE**: {citation_requirement}
- **LANGUAGE**: Formal academic English
- **STRUCTURE**: Follow academic paper conventions for {chapter_type} sections

## CITATION GUIDELINES
- Read each literature's ABSTRACT carefully before citing
- Only cite papers whose findings/methods directly support your statements
- Use the most relevant citekey based on the paper's actual content
- Each citation must have a clear connection to the cited paper's abstract
- Avoid generic citations - each citation should serve a specific purpose

## Writing Style Guide
{style_guide}

## Target Journal
{context.get("target_journal", "Academic Journal")}

## Current Context
{context.get("background", "No background provided")}

## Task Requirements
Write a high-quality academic {chapter_type} section that:
1. Uses LaTeX formatting (\\section{{Title}}, \\subsection{{Title}}, etc.)
2. Follows the style guide above exactly
3. Uses formal academic language and terminology
4. {citation_requirement.replace("EVERY sentence", "EVERY factual statement").replace("ONLY cite", "ONLY cite from")}
5. Maintains logical flow and coherence
6. Uses proper academic structure and transitions

## AVAILABLE LITERATURE (citekeys, bibtex, abstracts)
{context.get("literature_references", "No literature available - write without citations")}

**IMPORTANT**: Output ONLY the LaTeX-formatted section content. Do NOT include any explanations, markdown, or additional text."""
        return prompt

    def _get_citation_requirement(self, chapter_type: str) -> str:
        """根据章节类型返回引用要求"""
        citation_rules = {
            "introduction": "EVERY sentence containing factual claims, previous research, or background information MUST include a citation from the provided literature database",
            "discussion": "EVERY sentence comparing results with existing literature, discussing implications, or referencing previous studies MUST include a citation",
            "conclusion": "EVERY sentence referencing broader implications, future directions, or summarizing key findings with literature support MUST include a citation",
            "abstract": "Include citations only for specific findings or methods that require literature support",
            "methods": "ONLY cite established methods, protocols, or standards from the literature database - do not cite for basic/common procedures",
            "results": "ONLY cite statistical methods, analysis techniques, or comparative standards - do not cite for presenting your own findings",
            "materials": "ONLY cite established methods, protocols, or standards from the literature database - do not cite for basic/common procedures",
        }

        return citation_rules.get(
            chapter_type.lower(), "Cite relevant literature when appropriate"
        )

    def _call_ai(self, prompt: str, temperature: float = 0.7) -> str:
        """Call AI model"""
        messages = [{"role": "user", "content": prompt}]
        return self.api_client.call_model(self.model, messages, temperature)

    def _clean_content(self, content: str) -> str:
        """Clean the generated content"""
        # Remove any markdown formatting that shouldn't be there
        content = re.sub(r"^#+\s*", "", content, flags=re.MULTILINE)
        return content.strip()

    def _format_literature_for_prompt(
        self,
        literature: Union[List[Any], Dict[str, List[Any]]],
        reference_format: str = "nature",
    ) -> str:
        """
        Format literature for the prompt with citekey, bibtex, and abstract

        Args:
            literature: List of Paper objects or Dict of paragraph->papers
            reference_format: Reference format for BibTeX

        Returns:
            Formatted literature string for prompt
        """
        if not literature:
            return "No literature available - write without citations"

        # 如果输入是字典（按段落分组的文献），将其合并为一个列表
        if isinstance(literature, dict):
            all_papers = []
            for para_papers in literature.values():
                all_papers.extend(para_papers)
            literature = all_papers

        formatted_refs = []
        for paper in literature:
            # 获取citekey
            citekey = (
                getattr(paper, "citekey", "")
                or getattr(paper, "generate_citekey", lambda: "")()
            )
            if not citekey and hasattr(paper, "generate_citekey"):
                citekey = paper.generate_citekey()
            elif not citekey:
                # 从authors和year生成
                first_author = "Unknown"
                if hasattr(paper, "authors") and paper.authors:
                    parts = paper.authors.split(",")[0].split(";")[0].strip().split()
                    if parts:
                        first_author = parts[-1]
                year = getattr(paper, "year", 0) or 0
                citekey = f"{first_author}{year}"

            # 获取bibtex
            if hasattr(paper, "to_bibtex"):
                bibtex = paper.to_bibtex(reference_format)
            else:
                bibtex = ""

            # 获取abstract
            abstract = getattr(paper, "abstract", "") or ""

            ref_text = f"""
=== Literature Reference ===
citekey: {citekey}

bibtex:
{bibtex}

abstract:
{abstract}
"""
            formatted_refs.append(ref_text)

        return "\n".join(formatted_refs)


class IntroductionAgent(BaseAgent):
    """Agent for writing Introduction section in LaTeX format"""

    def __init__(self, api_client: APIClient, model: str = "gpt-4o"):
        super().__init__("IntroductionAgent", api_client, model)

    def write_section_with_skill(
        self, context: Dict[str, Any], skill: Dict[str, Any]
    ) -> str:
        """根据skill写作Introduction章节，同时参照风格指南"""
        style_guide = context.get("style_guide", "")
        literature = context.get("literature", [])
        citation_style = context.get("citation_style", {})
        reference_format = citation_style.get("reference_format", "nature")

        # Format literature with citekey, bibtex, abstract
        literature_references = self._format_literature_for_prompt(
            literature, reference_format
        )
        context["literature_references"] = literature_references

        prompt = self._build_system_prompt("introduction", style_guide, context)
        prompt += f"""

## WRITING SKILL GUIDANCE (PRIMARY REFERENCE)
{json.dumps(skill, ensure_ascii=False, indent=2)}

## EXECUTION INSTRUCTIONS (MANDATORY)
You MUST simultaneously reference BOTH files for writing:

### 1. SKILL FILE REFERENCE (结构和内容指导):
- Follow the paragraph structure and count specified in skill
- Cover all key messages and content outlines from skill
- Apply the rhetorical strategy and writing approach from skill
- Follow citation requirements exactly as specified in skill
- Ensure word count matches the estimates in skill

### 2. STYLE GUIDE REFERENCE (语言风格指导):
- Apply the writing style, tone, and language patterns from the style guide above
- Use vocabulary and expressions that match the journal's preferences
- Follow sentence structure patterns from the style guide
- Maintain the academic tone and formality level shown in the style guide

### 3. INTEGRATION APPROACH:
- Use skill file as the PRIMARY guide for WHAT to write (content structure)
- Use style guide as the PRIMARY guide for HOW to write (language style)
- Combine both seamlessly - content from skill, expression from style guide
- Prioritize skill's structural requirements while applying style guide's language norms

## AVAILABLE LITERATURE FOR CITATION
{literature_references}

Output the complete Introduction section in LaTeX format."""

        content = self._call_ai(prompt, temperature=0.7)
        return self._clean_content(content)

    def write_section(
        self, context: Dict[str, Any], requirements: Dict[str, Any]
    ) -> str:
        # 兼容旧代码：如果没有skill，使用传统方法
        return self.write_section_with_skill(context, {})


class MethodsAgent(BaseAgent):
    """Agent for writing Methods section in LaTeX format"""

    def __init__(self, api_client: APIClient, model: str = "gpt-4o"):
        super().__init__("MethodsAgent", api_client, model)

    def write_section(
        self, context: Dict[str, Any], requirements: Dict[str, Any]
    ) -> str:
        style_guide = context.get("style_guide", "")
        results_data = context.get("results_data", "")
        literature = context.get("literature", [])
        citation_style = context.get("citation_style", {})
        reference_format = citation_style.get("reference_format", "nature")

        # Format literature for methods (may reference methodological papers)
        literature_references = self._format_literature_for_prompt(
            literature[:5], reference_format
        )
        context["literature_references"] = literature_references

        prompt = self._build_system_prompt("Methods", style_guide, context)
        prompt += f"""

## Research Data Available
{results_data if results_data else "No specific data provided. Write a general methods section."}

## Methods Structure
Write a Methods section that includes:

\subsection{{Study Area/Site Description}}
Describe the location and environmental conditions. Cite location-specific studies if applicable.

\subsection{{Materials}}
List all materials, equipment, and reagents used.

\subsection{{Experimental Design and Procedures}}
Detail the study design, group allocation, and experimental procedures.
Use past tense throughout. Cite established methods only when describing non-standard protocols.

\subsection{{Data Collection Methods}}
Explain how data was collected and measured.

\subsection{{Statistical Analysis}}
Describe statistical methods used. Cite standard methods and software packages.

## CITATION REQUIREMENTS FOR METHODS
- **ONLY cite established protocols, methods, or standards from literature**
- **Do NOT cite for basic/common procedures** (e.g., don't cite for "we used SPSS software")
- **Cite ONLY when referencing specific methodological papers** that describe techniques you followed
- **Cite location-specific studies** only if they provide unique contextual information
- Read abstracts to ensure citations are for actual methodological references, not just general topics

Write in English, using past tense. Output LaTeX code only."""

        content = self._call_ai(prompt, temperature=0.7)
        return self._clean_content(content)


class ResultsAgent(BaseAgent):
    """Agent for writing Results section in LaTeX format"""

    def __init__(self, api_client: APIClient, model: str = "gpt-4o"):
        super().__init__("ResultsAgent", api_client, model)

    def write_section(
        self, context: Dict[str, Any], requirements: Dict[str, Any]
    ) -> str:
        style_guide = context.get("style_guide", "")
        results_data = context.get("results_data", "")
        literature = context.get("literature", [])
        citation_style = context.get("citation_style", {})
        reference_format = citation_style.get("reference_format", "nature")

        # Format literature for results (may compare with previous findings)
        literature_references = self._format_literature_for_prompt(
            literature[:5], reference_format
        )
        context["literature_references"] = literature_references

        prompt = self._build_system_prompt("Results", style_guide, context)
        prompt += f"""

## Research Results Data
{results_data if results_data else "No specific data provided. Write a general results section based on the background context."}

## Results Structure
Write a Results section that:

\subsection{{Main Findings}}
Present your primary findings in logical order. Use past tense for describing what was found.

\subsection{{Statistical Outcomes}}
Report all statistical tests, p-values, confidence intervals, and effect sizes.
Cite statistical methods or analysis techniques if they are non-standard.

\subsection{{Figures and Tables}}
Reference all figures and tables using \\ref{{fig:label}} and \\tabref{{tab:label}}.

\subsection{{Comparison with Previous Studies}}
Where relevant, compare your findings with previous research. Cite relevant literature.

## CITATION REQUIREMENTS FOR RESULTS
- **ONLY cite statistical methods** if referencing specific analytical techniques from literature
- **ONLY cite comparative standards** when your results need to be contextualized against established benchmarks
- **Do NOT cite for presenting your own data/findings**
- **Cite sparingly** - results sections should focus on your data, not literature review
- Read abstracts to ensure citations support specific analytical or comparative claims

Write in English, presenting factual information. Output LaTeX code only."""

        content = self._call_ai(prompt, temperature=0.7)
        return self._clean_content(content)


class DiscussionAgent(BaseAgent):
    """Agent for writing Discussion section in LaTeX format"""

    def __init__(self, api_client: APIClient, model: str = "claude-sonnet-4-20250514"):
        super().__init__("DiscussionAgent", api_client, model)

    def write_section(
        self, context: Dict[str, Any], requirements: Dict[str, Any]
    ) -> str:
        style_guide = context.get("style_guide", "")
        literature = context.get("literature", [])
        citation_style = context.get("citation_style", {})
        reference_format = citation_style.get("reference_format", "nature")

        # Format literature for discussion (critical comparison with existing work)
        literature_references = self._format_literature_for_prompt(
            literature[:10], reference_format
        )
        context["literature_references"] = literature_references

        prompt = self._build_system_prompt("Discussion", style_guide, context)
        prompt += f"""

## Discussion Structure
Write a Discussion section that includes:

\subsection{{Summary of Key Findings}}
Briefly restate your main findings (1 paragraph). Focus on your results - minimal citations.

\subsection{{Interpretation and Comparison with Existing Literature}}
2-3 paragraphs comparing your results with previous studies.
**EVERY comparison, interpretation, or reference to existing work MUST cite relevant literature.**

\subsection{{Theoretical and Practical Implications}}
1-2 paragraphs discussing implications of your findings.
Cite theoretical frameworks and related work that support your interpretations.

\subsection{{Study Limitations}}
1 paragraph acknowledging limitations. Cite methodological papers that discuss similar limitations.

\subsection{{Future Research Directions}}
1 paragraph suggesting future research directions. Cite literature that identifies gaps or suggests future work.

## CITATION REQUIREMENTS FOR DISCUSSION
- **EVERY sentence** that compares your results with existing literature MUST cite relevant papers
- **EVERY sentence** that discusses implications or theoretical frameworks MUST cite supporting literature
- **EVERY sentence** that suggests future directions MUST cite literature identifying gaps
- Read abstracts carefully - only cite papers whose findings directly relate to your discussion points
- Use multiple citations when discussing complex topics that span several studies

Write in English, using critical analytical thinking. Output LaTeX code only."""

        content = self._call_ai(prompt, temperature=0.7)
        return self._clean_content(content)


class AbstractAgent(BaseAgent):
    """Agent for writing Abstract section in LaTeX format"""

    def __init__(self, api_client: APIClient, model: str = "gpt-4o"):
        super().__init__("AbstractAgent", api_client, model)

    def write_section(
        self, context: Dict[str, Any], requirements: Dict[str, Any]
    ) -> str:
        style_guide = context.get("style_guide", "")
        literature = context.get("literature", [])
        citation_style = context.get("citation_style", {})
        reference_format = citation_style.get("reference_format", "nature")

        # Abstract typically doesn't include citations per many journal requirements
        context["literature_references"] = (
            "No citations in abstract per journal standards"
        )

        prompt = self._build_system_prompt("Abstract", style_guide, context)
        prompt += """
## Abstract Requirements
Write a comprehensive abstract (200-300 words) that includes:

\subsection*{Background/Objective}
1-2 sentences stating the research problem and objectives.

\subsection*{Methods}
1-2 sentences describing the study design and methods.

\subsection*{Results}
1-2 sentences presenting key findings with statistical outcomes.

\subsection*{Conclusions}
1-2 sentences stating main conclusions and implications.

## CITATION REQUIREMENTS FOR ABSTRACT
- **Most journals discourage citations in abstracts**
- **ONLY cite if absolutely essential** for establishing context or specific findings
- **Cite sparingly** - prefer to describe work without references
- If citing, ensure the citation is crucial and directly supports a key claim

\section*{Abstract}

Write your abstract here in LaTeX format...

Write in English, using formal academic language. Output LaTeX code only."""

        content = self._call_ai(prompt, temperature=0.5)
        return self._clean_content(content)


class ConclusionAgent(BaseAgent):
    """Agent for writing Conclusion section in LaTeX format"""

    def __init__(self, api_client: APIClient, model: str = "claude-sonnet-4-20250514"):
        super().__init__("ConclusionAgent", api_client, model)

    def write_section(
        self, context: Dict[str, Any], requirements: Dict[str, Any]
    ) -> str:
        style_guide = context.get("style_guide", "")
        literature = context.get("literature", [])
        citation_style = context.get("citation_style", {})
        reference_format = citation_style.get("reference_format", "nature")

        # Format literature for conclusions (future directions may reference gaps)
        literature_references = self._format_literature_for_prompt(
            literature[:3], reference_format
        )
        context["literature_references"] = literature_references

        prompt = self._build_system_prompt("Conclusion", style_guide, context)
        prompt += """
## Conclusion Structure
Write a Conclusion section that:

\subsection*{Main Findings}
1 paragraph restating your main findings concisely. Focus on your contributions.

\subsection*{Implications}
1 paragraph discussing the broader implications of your study.
Cite theoretical foundations or literature that supports your claims about significance.

\subsection*{Future Research Directions}
1 paragraph suggesting future research directions.
Cite literature that identifies gaps or suggests directions relevant to your work.

## CITATION REQUIREMENTS FOR CONCLUSION
- **Cite ONLY when discussing broader implications that require literature support**
- **Cite ONLY when suggesting future directions that build on existing literature**
- **Do NOT cite for restating your own findings**
- Read abstracts to ensure citations are directly relevant to your conclusion points
- Use citations sparingly - conclusions should focus on your work's contributions

Write in English, providing a strong closing to the paper. Output LaTeX code only."""

        content = self._call_ai(prompt, temperature=0.7)
        return self._clean_content(content)


class ConclusionAgent(BaseAgent):
    """Agent for writing Conclusion section in LaTeX format"""

    def __init__(self, api_client: APIClient, model: str = "claude-sonnet-4-20250514"):
        super().__init__("ConclusionAgent", api_client, model)

    def write_section(
        self, context: Dict[str, Any], requirements: Dict[str, Any]
    ) -> str:
        style_guide = context.get("style_guide", "")
        literature = context.get("literature", [])

        # Format literature for conclusions (future directions may reference gaps)
        literature_references = self._format_literature_for_prompt(literature[:3])
        context["literature_references"] = literature_references

        prompt = self._build_system_prompt("Conclusion", style_guide, context)
        prompt += """
## Conclusion Structure
Write a Conclusion section that:

\subsection*{Main Findings}
1 paragraph restating your main findings concisely. No citations needed.

\subsection*{Implications}
1 paragraph discussing the broader implications of your study.
Cite theoretical foundations if relevant.

\subsection*{Future Research Directions}
1 paragraph suggesting future research directions.
Cite gaps in the literature and emerging questions.

Use \\citep{{citekey}} for theoretical frameworks and future research recommendations.
**Minimize citations in conclusions - focus on your contributions.**
**Use ONLY citekeys from the literature database when citing external work.**

Write in English, providing a strong closing to the paper. Output LaTeX code only."""

        content = self._call_ai(prompt, temperature=0.7)
        return self._clean_content(content)


class MultiAgentCoordinator:
    """Coordinator for managing multiple writing agents"""

    def __init__(
        self, base_url: str, api_key: str, model_config: Optional[Dict[str, str]] = None
    ):
        self.api_client = APIClient(base_url, api_key)

        # Use provided model config or fall back to default
        if model_config is None:
            self.model_config = {
                section: config["model"]
                for section, config in SECTION_MODEL_CONFIG.items()
            }
        else:
            self.model_config = model_config

        # Agent registry
        self.agent_registry = {
            "introduction": IntroductionAgent,
            "methods": MethodsAgent,
            "results": ResultsAgent,
            "discussion": DiscussionAgent,
            "abstract": AbstractAgent,
            "conclusion": ConclusionAgent,
        }

        self.tasks: List[Task] = []
        self.results: Dict[str, SectionResult] = {}

    def extract_chapter_style_guide(self, full_style_guide: str, chapter: str) -> str:
        """Extract chapter-specific style guide"""
        chapter_patterns = {
            "introduction": r"## Introduction.*?(?=\n##|\Z)",
            "methods": r"## Methods.*?(?=\n##|\Z)",
            "results": r"## Results.*?(?=\n##|\Z)",
            "discussion": r"## Discussion.*?(?=\n##|\Z)",
            "conclusion": r"## Conclusion.*?(?=\n##|\Z)",
            "abstract": r"## Abstract.*?(?=\n##|\Z)",
        }

        pattern = chapter_patterns.get(chapter.lower())
        if pattern:
            match = re.search(pattern, full_style_guide, re.DOTALL | re.IGNORECASE)
            if match:
                return match.group(0).strip()

        return "Follow standard academic writing conventions for this section."

    def run_two_level_workflow(
        self,
        context: Dict[str, Any],
        progress_callback=None,
        sections: Optional[List[str]] = None,
        literature_db=None,
    ) -> Dict[str, SectionResult]:
        """运行两级AI写作工作流

        一级AI：生成详细写作skill
        二级AI：根据skill搜索文献并写作

        Args:
            context: 写作上下文（包含style_guide, research_content等）
            progress_callback: 进度回调函数
            sections: 要生成的章节列表
            literature_db: 文献数据库管理器

        Returns:
            各章节的写作结果
        """
        results = {}

        # 获取用户选择的章节
        if sections is None:
            sections = [
                "introduction",
                "methods",
                "results",
                "discussion",
                "conclusion",
            ]

        total_steps = len(sections) * 2  # 每个章节需要skill生成和写作两个步骤
        current_step = 0

        # 初始化一级AI（skill生成器）
        skill_generator = SkillGeneratorAgent(
            self.api_client, "claude-sonnet-4-20250514"
        )

        # 获取风格指南和研究内容
        style_guide = context.get("style_guide", "")
        research_content = (
            context.get("background", "") + "\n" + context.get("results_data", "")
        )

        for section_name in sections:
            if progress_callback:
                progress_callback(
                    current_step + 1,
                    total_steps,
                    f"生成{self._get_chinese_name(section_name)}skill",
                    0.1,
                )
            current_step += 1

            try:
                # 第一步：一级AI生成skill
                skill = skill_generator.generate_skill(
                    section_name=section_name,
                    context=context,
                    style_guide=style_guide,
                    research_content=research_content,
                )

                if progress_callback:
                    progress_callback(
                        current_step + 1,
                        total_steps,
                        f"根据skill写作{self._get_chinese_name(section_name)}",
                        0.1,
                    )
                current_step += 1

                # 第二步：二级AI根据skill写作
                # 获取对应的写作Agent
                writing_agent_class = self.agent_registry.get(section_name)
                if not writing_agent_class:
                    continue

                model = self.model_config.get(section_name, DEFAULT_MODEL)
                writing_agent = writing_agent_class(self.api_client, model)

                # 根据skill搜索相关文献（按段落）
                relevant_literature_dict = {}
                if literature_db and skill:
                    relevant_literature_dict = writing_agent.search_relevant_literature(
                        section_name, skill, literature_db, query_limit=15
                    )

                # 将所有段落的文献合并为一个列表
                relevant_literature = []
                for para_key, papers in relevant_literature_dict.items():
                    relevant_literature.extend(papers)

                # 去重（避免同一篇文献被多次引用）
                seen_ids = set()
                unique_literature = []
                for paper in relevant_literature:
                    paper_id = getattr(
                        paper, "id", getattr(paper, "wos_id", str(paper))
                    )
                    if paper_id not in seen_ids:
                        unique_literature.append(paper)
                        seen_ids.add(paper_id)

                # 更新上下文，包含skill和相关文献
                writing_context = context.copy()
                writing_context["skill"] = skill
                writing_context["literature"] = relevant_literature

                # 执行写作
                content = writing_agent.write_section_with_skill(writing_context, skill)

                # 计算结果
                word_count = len(content.split())
                citations = self._extract_citations(content)
                quality_score = self._calculate_quitation_quality_score(
                    content, section_name
                )

                results[section_name] = SectionResult(
                    section_name=section_name,
                    content=content,
                    word_count=word_count,
                    citations_used=citations,
                    quality_score=quality_score,
                    status=AgentStatus.COMPLETED,
                )

                if progress_callback:
                    progress_callback(
                        current_step,
                        total_steps,
                        f"{self._get_chinese_name(section_name)}完成",
                        1.0,
                    )

            except Exception as e:
                print(f"处理章节 {section_name} 时出错: {e}")
                results[section_name] = SectionResult(
                    section_name=section_name,
                    content="",
                    word_count=0,
                    citations_used=[],
                    quality_score=0.0,
                    status=AgentStatus.REJECTED,
                )

        # Step 4: 一级AI进行最终质量检查和风格调整
        if results:
            progress_callback(0.8, 1.0, "进行最终质量检查和风格调整", 0.8)
            results = self._final_quality_check_and_adjust(results, context)

        return results

    def _final_quality_check_and_adjust(
        self, chapter_results: Dict[str, SectionResult], context: Dict[str, Any]
    ) -> Dict[str, SectionResult]:
        """一级AI进行最终质量检查和风格调整

        Args:
            chapter_results: 各章节的写作结果
            context: 写作上下文

        Returns:
            调整后的章节结果
        """
        # 获取风格指南
        style_guide = context.get("style_guide", "")

        # 为每个章节进行质量检查和调整
        for section_name, result in chapter_results.items():
            if result.status != AgentStatus.COMPLETED:
                continue

            try:
                # 检查并调整章节内容
                adjusted_content = self._check_and_adjust_chapter_style(
                    section_name, result.content, style_guide
                )

                # 更新结果
                if adjusted_content != result.content:
                    result.content = adjusted_content
                    print(f"章节 {section_name} 经过风格调整")

            except Exception as e:
                print(f"调整章节 {section_name} 时出错: {e}")
                continue

        return chapter_results

    def _check_and_adjust_chapter_style(
        self, section_name: str, content: str, style_guide: str
    ) -> str:
        """检查并调整章节风格

        Args:
            section_name: 章节名称
            content: 章节内容
            style_guide: 风格指南

        Returns:
            调整后的内容
        """
        # 创建一级AI实例
        skill_generator = SkillGeneratorAgent(
            self.api_client, "claude-sonnet-4-20250514"
        )

        prompt = f"""你是一级AI质量检查专家。请检查以下{self._get_chinese_name(section_name)}章节内容是否符合学术期刊风格要求。

## 章节内容
{content}

## 目标期刊风格指南
{style_guide}

## 检查要求
1. **语言风格**: 是否符合学术论文的正式语气？
2. **句子结构**: 是否使用复杂的学术句式？
3. **词汇选择**: 是否使用领域专用术语？
4. **表达方式**: 是否符合期刊的表达偏好？
5. **学术规范**: 是否遵循学术写作规范？

## 调整指示
如果发现不符合风格要求的地方，请进行微调：
- 保持原文的核心内容和逻辑结构不变
- 只调整语言表达和风格问题
- 确保调整后的内容更加符合期刊风格
- 不要改变事实内容或引用

## 输出要求
如果内容已经符合风格要求，返回原文。
如果需要调整，返回调整后的完整章节内容。
只返回章节内容，不要其他说明。"""

        # 调用AI进行检查和调整
        adjusted_content = skill_generator._call_ai(prompt, temperature=0.3)

        # 清理内容
        adjusted_content = adjusted_content.strip()

        # 如果内容基本相同，认为不需要调整
        if self._content_similarity_check(content, adjusted_content) > 0.9:
            return content

        return adjusted_content

    def _content_similarity_check(self, original: str, adjusted: str) -> float:
        """检查内容相似度"""
        if len(original) == 0 or len(adjusted) == 0:
            return 0.0

        # 简单相似度检查：比较共同词的数量
        original_words = set(original.lower().split())
        adjusted_words = set(adjusted.lower().split())

        intersection = len(original_words.intersection(adjusted_words))
        union = len(original_words.union(adjusted_words))

        return intersection / union if union > 0 else 0.0

    def _get_chinese_name(self, section_name: str) -> str:
        """获取章节中文名"""
        names = {
            "introduction": "引言",
            "methods": "方法",
            "results": "结果",
            "discussion": "讨论",
            "abstract": "摘要",
            "conclusion": "结论",
        }
        return names.get(section_name, section_name)

    def run_workflow(
        self,
        context: Dict[str, Any],
        progress_callback=None,
        sections: Optional[List[str]] = None,
    ) -> Dict[str, SectionResult]:
        """Run the complete writing workflow

        Args:
            context: 写作上下文
            progress_callback: 进度回调函数
            sections: 要生成的章节列表，如果为None则生成所有章节
        """
        # 默认生成所有章节
        default_sections = [
            ("introduction", "引言"),
            ("methods", "方法"),
            ("results", "结果"),
            ("discussion", "讨论"),
            ("abstract", "摘要"),
            ("conclusion", "结论"),
        ]

        if sections is None:
            sections_order = default_sections
        else:
            # 将用户选择的章节转换为带中文名的列表
            section_names_cn = {
                "introduction": "引言",
                "methods": "方法",
                "results": "结果",
                "discussion": "讨论",
                "abstract": "摘要",
                "conclusion": "结论",
            }
            sections_order = [
                (s, section_names_cn.get(s, s))
                for s in sections
                if s in self.agent_registry
            ]

        total_steps = len(sections_order)

        for idx, (section_name, section_cn_name) in enumerate(sections_order):
            step = idx + 1

            if progress_callback:
                progress_callback(step, total_steps, section_name, step / total_steps)

            try:
                # Create agent with section-specific model
                agent_class = self.agent_registry.get(section_name)
                if not agent_class:
                    raise ValueError(f"Agent not found: {section_name}")

                model = self.model_config.get(section_name, DEFAULT_MODEL)
                agent = agent_class(self.api_client, model)

                # Get chapter-specific style guide
                full_style_guide = context.get("style_guide", "")
                chapter_style_guide = self.extract_chapter_style_guide(
                    full_style_guide, section_name
                )

                # Update context with chapter-specific guide
                task_context = context.copy()
                task_context["style_guide"] = chapter_style_guide

                # Write section
                start_time = time.time()
                content = agent.write_section(task_context, {})
                duration = time.time() - start_time

                # Calculate word count
                word_count = len(content.split())

                # Extract citations used
                citations = self._extract_citations(content)

                # Calculate quality score
                quality_score = self._calculate_quitation_quality_score(
                    content, section_name
                )

                # Create result
                result = SectionResult(
                    section_name=section_name,
                    content=content,
                    word_count=word_count,
                    citations_used=citations,
                    quality_score=quality_score,
                    status=AgentStatus.COMPLETED,
                )

                self.results[section_name] = result

            except Exception as e:
                # Create failed result
                result = SectionResult(
                    section_name=section_name,
                    content=f"Failed to write {section_name}: {str(e)}",
                    word_count=0,
                    citations_used=[],
                    quality_score=0.0,
                    status=AgentStatus.REJECTED,
                )
                self.results[section_name] = result

        return self.results

    def _extract_citations(self, content: str) -> List[str]:
        """Extract citations from LaTeX content"""
        # Pattern for LaTeX citations: \citep{key} or \citet{key}
        pattern = r"\\(?:paren)?cite(?:p|t)?\{([^}]+)\}"
        matches = re.findall(pattern, content)

        # Also check for author-year format in parentheses
        pattern2 = r"\(([A-Z][a-z]+(?: et al\.)?,?\s*\d{4})"
        matches2 = re.findall(pattern2, content)

        all_citations = list(set(matches + matches2))
        return all_citations

    def _calculate_quitation_quality_score(
        self, content: str, section_name: str
    ) -> float:
        """Calculate quality score for the content including citation quality"""
        if not content:
            return 0.0

        score = 0.3  # Base score

        # Check length
        word_count = len(content.split())
        if section_name == "abstract":
            if 150 <= word_count <= 350:
                score += 0.2
        elif section_name == "introduction":
            if 300 <= word_count <= 800:
                score += 0.2
        elif section_name == "methods":
            if 300 <= word_count <= 700:
                score += 0.2
        elif section_name == "results":
            if 300 <= word_count <= 800:
                score += 0.2
        elif section_name == "discussion":
            if 400 <= word_count <= 1000:
                score += 0.2
        elif section_name == "conclusion":
            if 150 <= word_count <= 400:
                score += 0.2

        # Check for proper structure (paragraphs)
        if "\\par" in content or "\n\n" in content:
            score += 0.1

        # Check for LaTeX citations (except abstract)
        if section_name != "abstract":
            if re.search(r"\\(?:paren)?cite(?:p|t)?\{", content):
                score += 0.2

        # Check for academic vocabulary
        academic_words = [
            "however",
            "therefore",
            "furthermore",
            "moreover",
            "consequently",
        ]
        found_words = [w for w in academic_words if w.lower() in content.lower()]
        if len(found_words) >= 2:
            score += 0.1

        return min(score, 1.0)

    def generate_references_section(
        self, literature: List[Any], used_citations: List[str]
    ) -> str:
        """
        Generate a LaTeX references section with all used citations

        Args:
            literature: List of Paper objects from database
            used_citations: List of citekeys used in the paper

        Returns:
            LaTeX-formatted references section
        """
        if not used_citations or not literature:
            return "% No references available"

        # Build a mapping of citekey -> paper
        citekey_to_paper = {}
        for paper in literature:
            citekey = getattr(paper, "citekey", "") or paper.generate_citekey()
            citekey_to_paper[citekey] = paper

        # Filter to only used citations
        used_papers = []
        for citekey in used_citations:
            # Handle comma-separated citekeys (e.g., \citep{key1,key2})
            for key in citekey.split(","):
                key = key.strip()
                if key in citekey_to_paper:
                    if citekey_to_paper[key] not in used_papers:
                        used_papers.append(citekey_to_paper[key])

        if not used_papers:
            return "% No cited papers found in database"

        # Generate references section header
        references_section = """
\section*{References}
\section{{References}}

\begin{thebibliography}}{{99}}

"""

        # Generate each reference
        for paper in used_papers:
            citekey = getattr(paper, "citekey", "") or paper.generate_citekey()

            # Format authors
            authors = paper.authors.replace(";", ", ")
            if " and " in authors:
                # Convert to "Author1, Author2, and Author3" format
                parts = authors.split(" and ")
                if len(parts) > 1:
                    authors = ", ".join(parts[:-1]) + ", and " + parts[-1]

            # Format: Authors (Year). Title. Journal, Volume(Issue), Pages.
            if paper.year > 0:
                ref_text = f"{authors} ({paper.year}). {paper.title}. {paper.journal}"
                if paper.volume:
                    ref_text += f", {paper.volume}"
                    if paper.issue:
                        ref_text += f"({paper.issue})"
                if paper.pages:
                    ref_text += f", {paper.pages}"
                ref_text += "."
            else:
                ref_text = f"{authors}. {paper.title}. {paper.journal}."

            references_section += f"\\bibitem{{{citekey}}} {ref_text}\n\n"

        references_section += "\\end{thebibliography}\n"

        return references_section

    def generate_bibliography_file(
        self, literature: List[Any], used_citations: List[str], output_path: str
    ) -> str:
        """
        Generate a standalone .bib file for the paper

        Args:
            literature: List of Paper objects from database
            used_citations: List of citekeys used in the paper
            output_path: Path to save the .bib file

        Returns:
            Path to the generated .bib file
        """
        # Build a mapping of citekey -> paper
        citekey_to_paper = {}
        for paper in literature:
            citekey = getattr(paper, "citekey", "") or paper.generate_citekey()
            citekey_to_paper[citekey] = paper

        # Filter to only used citations
        used_papers = []
        for citekey in used_citations:
            for key in citekey.split(","):
                key = key.strip()
                if key in citekey_to_paper:
                    if citekey_to_paper[key] not in used_papers:
                        used_papers.append(citekey_to_paper[key])

        # Generate BibTeX content
        bibtex_entries = []
        for paper in used_papers:
            bibtex_entries.append(paper.to_bibtex())

        bibtex_content = "\n\n".join(bibtex_entries)

        # Save to file
        Path(output_path).write_text(bibtex_content, encoding="utf-8")

        return output_path


# Alias for backward compatibility
PaperWritingCoordinator = MultiAgentCoordinator
