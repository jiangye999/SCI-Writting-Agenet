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
from typing import Any, Dict, List, Optional, Tuple
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


class BaseAgent:
    """Base class for all writing agents with LaTeX output support"""

    def __init__(self, name: str, api_client: APIClient, model: str = "gpt-4o"):
        self.name = name
        self.api_client = api_client
        self.model = model

    def write_section(
        self, context: Dict[str, Any], requirements: Dict[str, Any]
    ) -> str:
        raise NotImplementedError

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
        self, literature: List[Any], reference_format: str = "nature"
    ) -> str:
        """
        Format literature for the prompt with citekey, bibtex, and abstract

        Args:
            literature: List of Paper objects
            reference_format: Reference format for BibTeX

        Returns:
            Formatted literature string for prompt
        """
        if not literature:
            return "No literature available - write without citations"

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

    def write_section(
        self, context: Dict[str, Any], requirements: Dict[str, Any]
    ) -> str:
        style_guide = context.get("style_guide", "")
        literature = context.get("literature", [])
        citation_style = context.get("citation_style", {})
        reference_format = citation_style.get("reference_format", "nature")

        # Format literature with citekey, bibtex, abstract
        literature_references = self._format_literature_for_prompt(
            literature, reference_format
        )
        context["literature_references"] = literature_references

        prompt = self._build_system_prompt("Introduction", style_guide, context)
        prompt += f"""

## Introduction Structure
Write an Introduction section that follows this structure:

\subsection{{Background and Context}}
2-3 paragraphs establishing the research field and context. EVERY factual claim about previous research MUST be cited with relevant literature.

\subsection{{Problem Statement and Research Gap}}
1-2 paragraphs identifying the gap in current knowledge. EVERY claim about existing knowledge or gaps MUST cite relevant literature.

\subsection{{Research Objectives and Significance}}
1 paragraph stating your objectives and the significance of this study. Cite foundational work that supports your research importance.

## CITATION REQUIREMENTS FOR INTRODUCTION
- **EVERY sentence** that mentions previous research, existing knowledge, or background information **MUST cite relevant literature**
- Read each paper's ABSTRACT to find the most appropriate citation
- Cite specific findings or methods from the literature that directly relate to your topic
- Use citations to establish credibility and context for your research

Write in English, following academic conventions. Output LaTeX code only."""

        content = self._call_ai(prompt, temperature=0.7)
        return self._clean_content(content)


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
