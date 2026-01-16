#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI增强的期刊风格分析器
严格按照journal_section_style_skill.md的标准化流程工作
"""

import json
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Any
import requests
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed


@dataclass
class StyleDimension:
    """风格维度数据类"""

    function: List[str] = field(default_factory=list)
    role: str = ""
    information_structure: List[str] = field(default_factory=list)
    information_density: Dict[str, Any] = field(default_factory=dict)
    stance_hedging: Dict[str, Any] = field(default_factory=dict)
    sentence_patterns: List[Dict[str, str]] = field(default_factory=list)
    lexical_features: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    constraints: Dict[str, List[str]] = field(default_factory=dict)


@dataclass
class SectionStyleCard:
    """章节风格卡片"""

    section_name: str
    journal_name: str
    analysis_date: str
    sample_size: int
    dimensions: StyleDimension


class AIDeepSeekAnalyzer:
    """基于DeepSeek的AI增强风格分析器 - 严格按照skill标准化流程工作"""

    def __init__(self, api_key: str, base_url: str = "https://api.deepseek.com/v1"):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = "deepseek-chat"
        self.skill_file_path = (
            r"E:\AI_projects\学术写作\paper_writer\journal_section_style_skill.md"
        )

    def load_skill_definition(self) -> str:
        """加载skill定义文件"""
        try:
            with open(self.skill_file_path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            raise FileNotFoundError(f"Skill file not found: {self.skill_file_path}")
        except Exception as e:
            raise Exception(f"Failed to load skill file: {e}")

    def extract_paper_sections(
        self, paper_text: str, journal_name: str
    ) -> Dict[str, str]:
        """
        让DeepSeek提取论文的所有章节

        Args:
            paper_text: 完整论文文本
            journal_name: 期刊名称

        Returns:
            Dict[str, str]: 章节名称到章节内容的映射
        """
        skill_content = self.load_skill_definition()

        prompt = f"""You are an expert academic paper analyst. First, carefully read and understand this skill definition:

{skill_content}

Now, your task is to extract ALL identifiable sections from the provided academic paper. Follow these steps:

1. Read the entire paper carefully
2. Identify all major sections (Abstract, Introduction, Methods, Results, Discussion, Conclusion, etc.)
3. Extract the exact text content of each section
4. Return the sections in a structured JSON format

Paper to analyze:
{journal_name} Paper Text:
{paper_text[:15000]}...(truncated for length)

Return ONLY a valid JSON object with this exact structure:
{{
    "abstract": "full abstract text here",
    "introduction": "full introduction text here",
    "methods": "full methods text here",
    "results": "full results text here",
    "discussion": "full discussion text here",
    "conclusion": "full conclusion text here"
}}

If a section is not found, use an empty string for that section. Do not include any other text or explanations."""

        response = self._call_deepseek_api(prompt)

        try:
            if isinstance(response, str):
                sections = json.loads(response)
            else:
                sections = response
            return sections
        except json.JSONDecodeError:
            # 如果解析失败，返回空字典
            print(f"Failed to parse section extraction response: {response}")
            return {}

    def analyze_section_with_skill(
        self, section_samples: List[str], section_name: str, journal_name: str
    ) -> Dict[str, Any]:
        """
        严格按照skill要求分析章节风格

        Args:
            section_samples: 该章节的所有样本文本
            section_name: 章节名称
            journal_name: 期刊名称

        Returns:
            Dict[str, Any]: 按照skill标准的Section Style Card格式分析结果
        """
        skill_content = self.load_skill_definition()

        # 检查样本数量
        if len(section_samples) < 5:
            print(
                f"Warning: Only {len(section_samples)} samples provided, skill requires ≥5 samples"
            )

        # 合并所有样本文本
        combined_samples = "\n\n--- SAMPLE SEPARATOR ---\n\n".join(section_samples)

        prompt = f"""You are an expert academic writing style analyst. Your task is to create a Section Style Card following the skill definition EXACTLY.

First, carefully read and understand this skill definition:
{skill_content}

CRITICAL REQUIREMENTS:
1. You MUST produce a Section Style Card with ALL 8 dimensions
2. Each dimension MUST follow the exact format specified in the skill
3. Do NOT skip any dimension or modify the required structure

Now analyze the "{section_name}" section from {len(section_samples)} sample papers.

Sample texts to analyze:
{combined_samples[:10000]}...(truncated for length)

Return your analysis in this exact Section Style Card JSON structure:
{{
    "section_name": "{section_name}",
    "journal": "{journal_name}",
    "sample_count": {len(section_samples)},
    "function": {{
        "requirements": [
            "Must + action + object (format 1)",
            "Must + action + object (format 2)",
            "Must + action + object (format 3)"
        ],
        "communicative_goals": "Brief description of what this section must accomplish"
    }},
    "role_in_paper": {{
        "description": "1 short paragraph defining how this section contributes to the full paper logic",
        "contribution_type": "setup/evidence/interpretation/closure"
    }},
    "information_structure": {{
        "rhetorical_moves": [
            "1. Move name (mandatory)",
            "2. Move name (mandatory)",
            "3. Move name (optional)"
        ],
        "flow_description": "Stepwise path description"
    }},
    "information_density": {{
        "high_detail": "What 'high detail' looks like in this journal",
        "low_detail": "What 'high-level summary' looks like in this journal",
        "typical_range": "Description of typical density range"
    }},
    "stance_hedging": {{
        "intensity_band": "cautious/moderately assertive/assertive",
        "author_voice": "explicit author voice vs. impersonal tone",
        "claim_strength": "strong claims vs. qualified claims",
        "certainty_level": "Description of acceptable certainty level"
    }},
    "sentence_pattern_functions": [
        {{
            "function": "Communicative job description",
            "typical_position": "paragraph start/middle/end",
            "journal_preference": "journal-specific vs. general academic"
        }},
        {{
            "function": "Communicative job description 2",
            "typical_position": "paragraph position 2",
            "journal_preference": "preference 2"
        }},
        {{
            "function": "Communicative job description 3",
            "typical_position": "paragraph position 3",
            "journal_preference": "preference 3"
        }},
        {{
            "function": "Communicative job description 4",
            "typical_position": "paragraph position 4",
            "journal_preference": "preference 4"
        }},
        {{
            "function": "Communicative job description 5",
            "typical_position": "paragraph position 5",
            "journal_preference": "preference 5"
        }},
        {{
            "function": "Communicative job description 6",
            "typical_position": "paragraph position 6",
            "journal_preference": "preference 6"
        }}
    ],
    "lexical_features_by_pos": {{
        "nouns": {{
            "top_35": ["word1", "word2", ...],
            "semantic_orientation": "abstract/technical/evaluative",
            "refer_to": "object/actor/action/value/evidence",
            "intensify_soften_neutral": "intensify/soften/neutral",
            "profile_summary": "3-6 bullet points summary"
        }},
        "verbs": {{
            "top_35": ["word1", "word2", ...],
            "semantic_orientation": "abstract/technical/evaluative",
            "refer_to": "object/actor/action/value/evidence",
            "intensify_soften_neutral": "intensify/soften/neutral",
            "profile_summary": "3-6 bullet points summary"
        }},
        "adjectives": {{
            "top_35": ["word1", "word2", ...],
            "semantic_orientation": "abstract/technical/evaluative",
            "refer_to": "object/actor/action/value/evidence",
            "intensify_soften_neutral": "intensify/soften/neutral",
            "profile_summary": "3-6 bullet points summary"
        }},
        "adverbs": {{
            "top_35": ["word1", "word2", ...],
            "semantic_orientation": "abstract/technical/evaluative",
            "refer_to": "object/actor/action/value/evidence",
            "intensify_soften_neutral": "intensify/soften/neutral",
            "profile_summary": "3-6 bullet points summary"
        }}
    }},
    "constraints_and_avoidances": {{
        "do": [
            "Do item 1",
            "Do item 2",
            "Do item 3"
        ],
        "dont": [
            "Don't item 1", 
            "Don't item 2",
            "Don't item 3"
        ],
        "boundary_rules": "What not to do in this section"
    }}
}}

REQUIREMENTS CHECKLIST:
- ✓ All 8 dimensions included
- ✓ Function has 3-5 "Must + action + object" requirements
- ✓ Role is exactly 1 short paragraph
- ✓ Information structure has mandatory/optional moves
- ✓ Stance & hedging defines intensity band
- ✓ Sentence patterns have exactly 6 categories
- ✓ Lexical features cover N/V/Adj/Adv with top 35 words (EXCLUDING: the, a, an, is, are, was, were, be, been, being, have, has, had, do, does, did, will, would, could, should, may, might, must, shall, can, need, soil, study, paper, research, result, data, fig, table, etc.)
- ✓ Constraints have Do/Don't lists (3-7 each)
- ✓ Top words must be meaningful academic vocabulary, NOT common stop words

IMPORTANT: For "top_35" fields:
- EXCLUDE all common stop words: the, a, an, is, are, was, were, be, been, being, have, has, had, do, does, did, will, would, could, should, may, might, must, shall, can, need, may, might
- EXCLUDE generic academic words: study, paper, research, result, results, data, fig, table, section, example, use, used, using, show, showed, shown, find, found, finding, suggest, suggested, suggests, indicate, indicated, indicates
- EXCLUDE common words: we, our, this, these, those, that, which, who, what, when, where, why, how, all, each, every, both, few, more, most, other, some, such, no, nor, not, only, own, same, so, than, too, very, just, also
- Include ONLY meaningful domain-specific vocabulary relevant to the section content
- Provide exactly 35 words for each POS category

Return ONLY the valid JSON object. No additional text or explanations."""

        # 调用API并验证结果
        max_retries = 3
        retry_count = 0

        while retry_count < max_retries:
            response = self._call_deepseek_api(prompt)

            # 检查响应是否为空或无效
            if not response or response.strip() == "":
                print(f"Empty response from API, retry {retry_count + 1}/{max_retries}")
                retry_count += 1
                continue

            # 清理响应：去除markdown代码块标记
            cleaned_response = response.strip()
            if cleaned_response.startswith("```"):
                # 去除 ```json 或 ``` 开头
                lines = cleaned_response.split("\n")
                if lines[0].startswith("```"):
                    lines = lines[1:]
                # 去除结尾的 ```
                if lines and lines[-1].strip() == "```":
                    lines = lines[:-1]
                cleaned_response = "\n".join(lines)

            # 尝试解析JSON
            try:
                analysis_result = (
                    json.loads(cleaned_response)
                    if isinstance(cleaned_response, str)
                    else cleaned_response
                )

                # 验证结果格式
                if self._validate_section_style_card(analysis_result):
                    return analysis_result
                else:
                    print(f"Validation failed, retry {retry_count + 1}/{max_retries}")
                    retry_count += 1
                    continue

            except json.JSONDecodeError as e:
                print(f"JSON parsing error: {e}, retry {retry_count + 1}/{max_retries}")
                print(f"Response preview: {response[:500] if response else 'empty'}")
                retry_count += 1
                continue

        print("Validation failed: Result doesn't match Section Style Card format")
        return {}

    def _validate_section_style_card(self, result: Dict[str, Any]) -> bool:
        """验证Section Style Card格式是否符合skill要求"""
        required_dimensions = [
            "function",
            "role_in_paper",
            "information_structure",
            "information_density",
            "stance_hedging",
            "sentence_pattern_functions",
            "lexical_features_by_pos",
            "constraints_and_avoidances",
        ]

        # 检查所有必需维度
        for dimension in required_dimensions:
            if dimension not in result:
                print(f"Missing required dimension: {dimension}")
                return False

        # 验证function格式
        if (
            not isinstance(result["function"].get("requirements"), list)
            or len(result["function"]["requirements"]) < 3
            or len(result["function"]["requirements"]) > 5
        ):
            print("Function must have 3-5 requirements")
            return False

        # 验证sentence patterns数量
        if (
            not isinstance(result["sentence_pattern_functions"], list)
            or len(result["sentence_pattern_functions"]) != 6
        ):
            print("Sentence patterns must have exactly 6 categories")
            return False

        # 验证lexical features
        required_pos = ["nouns", "verbs", "adjectives", "adverbs"]
        for pos in required_pos:
            if pos not in result["lexical_features_by_pos"]:
                print(f"Missing lexical features for {pos}")
                return False
            # 验证top_35字段
            pos_features = result["lexical_features_by_pos"][pos]
            if "top_35" not in pos_features:
                print(f"Missing top_35 in {pos}")
                return False
            if not isinstance(pos_features["top_35"], list):
                print(f"top_35 must be a list in {pos}")
                return False

        # 验证constraints格式
        if (
            "do" not in result["constraints_and_avoidances"]
            or "dont" not in result["constraints_and_avoidances"]
        ):
            print("Constraints must have 'do' and 'dont' lists")
            return False

        return True

    def _build_analysis_prompt(
        self, section_name: str, combined_text: str, skill_definition: str
    ) -> str:
        """构建AI分析提示词"""

        # 提取相关skill定义
        section_skill = self._extract_section_skill(skill_definition, section_name)

        prompt = f"""You are an expert academic writing analyst specializing in journal style analysis.

Your task is to analyze the writing style of the "{section_name}" section from {len(combined_text.split("--- SAMPLE SEPARATOR ---"))} sample papers.

Based on the following skill definition and sample texts, extract exactly 8 dimensions of writing style:

{skill_definition}

SECTION TO ANALYZE: {section_name}

SAMPLE TEXTS:
{combined_text[:8000]}... (truncated for length)

Please analyze and provide a complete Section Style Card with all 8 dimensions:

1. Function (3-5 hard requirements)
2. Role in the paper (1 short paragraph)
3. Information structure (stepwise path with mandatory/optional moves)
4. Information density (detail level range)
5. Stance & hedging (acceptable intensity band)
6. Sentence-pattern functions (exactly 6 categories with function, position, preference)
7. Lexical features by POS (N/V/Adj/Adv profiles based on top frequent items)
8. Constraints & avoidances (Do/Don't list)

Format your response as a structured JSON object."""

        return prompt

    def _extract_section_skill(self, skill_definition: str, section_name: str) -> str:
        """从skill定义中提取相关章节的定义"""
        # 简单的文本提取逻辑
        patterns = {
            "introduction": r"# 3\.1 Introduction.*?(?=# 3\.2|\Z)",
            "methods": r"# 3\.3 Methods.*?(?=# 3\.4|\Z)",
            "results": r"# 3\.4 Results.*?(?=# 3\.5|\Z)",
            "discussion": r"# 3\.5 Discussion.*?(?=# 4\.|\Z)",
        }

        pattern = patterns.get(section_name.lower(), r"#.*")
        match = re.search(pattern, skill_definition, re.DOTALL | re.IGNORECASE)

        return match.group(0) if match else skill_definition

    def _call_deepseek_api(self, prompt: str) -> str:
        """调用DeepSeek API - 返回原始响应字符串"""
        url = f"{self.base_url}/chat/completions"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        data = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are an expert academic writing style analyst. You must output valid JSON format only.",
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.3,
            "max_tokens": 4000,
        }

        try:
            response = requests.post(url, headers=headers, json=data, timeout=120)
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"]

        except requests.exceptions.Timeout:
            print("DeepSeek API timeout (120s), retrying...")
            # 重试一次
            try:
                response = requests.post(url, headers=headers, json=data, timeout=180)
                response.raise_for_status()
                result = response.json()
                return result["choices"][0]["message"]["content"]
            except Exception as e2:
                print(f"DeepSeek API retry failed: {e2}")
                return ""
        except Exception as e:
            print(f"DeepSeek API call failed: {e}")
            return ""

    def _parse_ai_response(
        self, response: Dict[str, Any], section_name: str
    ) -> StyleDimension:
        """解析AI响应并构建StyleDimension对象"""
        dimensions = StyleDimension()

        try:
            # 解析各个维度
            dimensions.function = response.get("function", [])
            dimensions.role = response.get("role", "")
            dimensions.information_structure = response.get("information_structure", [])
            dimensions.information_density = response.get("information_density", {})
            dimensions.stance_hedging = response.get("stance_hedging", {})
            dimensions.sentence_patterns = response.get("sentence_patterns", [])
            dimensions.lexical_features = response.get("lexical_features", {})
            dimensions.constraints = response.get("constraints", {"do": [], "dont": []})

        except Exception as e:
            print(f"Failed to parse AI response: {e}")

        return dimensions

    def _get_current_date(self) -> str:
        """获取当前日期"""
        from datetime import datetime

        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class R2RRAGEnhancer:
    """R2R RAG增强器 - 实现检索增强生成"""

    def __init__(self, api_key: str, base_url: str = "https://api.deepseek.com/v1"):
        self.deepseek_analyzer = AIDeepSeekAnalyzer(api_key, base_url)
        self.document_store = {}  # 简单的文档存储

    def enhance_with_rag(
        self,
        section_texts: List[str],
        section_name: str,
        journal_name: str,
    ) -> SectionStyleCard:
        """
        使用R2R RAG增强的风格分析

        Args:
            section_texts: 章节文本列表
            section_name: 章节名称
            journal_name: 期刊名称
            skill_file_path: skill定义文件路径

        Returns:
            SectionStyleCard: 增强的风格分析结果
        """

        # 1. 构建文档存储 - 将文本分块
        self._build_document_store(section_texts, section_name)

        # 2. 检索相关文本片段
        relevant_chunks = self._retrieve_relevant_chunks(section_name, top_k=5)

        # 3. 使用检索增强的内容进行AI分析
        analysis_result = self.deepseek_analyzer.analyze_section_with_skill(
            relevant_chunks, section_name, journal_name
        )

        # 转换为SectionStyleCard格式 - 适配新的JSON结构
        function_data = analysis_result.get("function", {})
        role_data = analysis_result.get("role_in_paper", {})
        structure_data = analysis_result.get("information_structure", {})
        density_data = analysis_result.get("information_density", {})
        stance_data = analysis_result.get("stance_hedging", {})
        patterns_data = analysis_result.get("sentence_pattern_functions", [])
        lexical_data = analysis_result.get("lexical_features_by_pos", {})
        constraints_data = analysis_result.get("constraints_and_avoidances", {})

        dimensions = StyleDimension(
            function=function_data.get("requirements", []),
            role=role_data.get("description", ""),
            information_structure=structure_data.get("rhetorical_moves", []),
            information_density={
                "high": density_data.get("high_detail", ""),
                "low": density_data.get("low_detail", ""),
            },
            stance_hedging={
                "band": stance_data.get("intensity_band", ""),
                "presence": stance_data.get("author_voice", ""),
            },
            sentence_patterns=patterns_data,
            lexical_features=lexical_data,
            constraints={
                "do": constraints_data.get("do", []),
                "dont": constraints_data.get("dont", []),
            },
        )

        style_card = SectionStyleCard(
            section_name=section_name,
            journal_name=journal_name,
            analysis_date=self.deepseek_analyzer._get_current_date(),
            sample_size=len(relevant_chunks),
            dimensions=dimensions,
        )

        return style_card

    def _build_document_store(self, section_texts: List[str], section_name: str):
        """构建文档存储，将文本分块"""
        chunks = []
        chunk_size = 1000  # 每个chunk约1000字符
        overlap = 200  # 重叠200字符

        for text in section_texts:
            # 简单分块策略
            words = text.split()
            for i in range(0, len(words), chunk_size - overlap):
                chunk_words = words[i : i + chunk_size]
                chunk = " ".join(chunk_words)
                if len(chunk.strip()) > 100:  # 只保留有意义的chunk
                    chunks.append(
                        {
                            "text": chunk,
                            "section": section_name,
                            "chunk_id": f"{section_name}_{len(chunks)}",
                            "metadata": {
                                "word_count": len(chunk_words),
                                "source": f"sample_{len(chunks) % len(section_texts)}",
                            },
                        }
                    )

        self.document_store[section_name] = chunks

    def _retrieve_relevant_chunks(self, section_name: str, top_k: int = 5) -> List[str]:
        """检索最相关的文本片段"""
        if section_name not in self.document_store:
            return []

        chunks = self.document_store[section_name]

        # 简单的检索策略：选择多样化的样本
        # 在实际RAG系统中，这里会使用语义相似度或其他检索算法
        selected_chunks = []
        seen_sources = set()

        # 优先选择不同的来源
        for chunk in chunks:
            source = chunk["metadata"]["source"]
            if source not in seen_sources and len(selected_chunks) < top_k:
                selected_chunks.append(chunk["text"])
                seen_sources.add(source)

        # 如果还没有足够样本，随机补充
        for chunk in chunks:
            if len(selected_chunks) >= top_k:
                break
            if chunk["text"] not in selected_chunks:
                selected_chunks.append(chunk["text"])

        return selected_chunks[:top_k]


def analyze_journal_style_with_ai(
    papers_dir: str,
    output_dir: str,
    journal_name: str,
    deepseek_api_key: str,
) -> Dict[str, str]:
    """
    基于DeepSeek和skill的完整期刊风格分析流程（重写版）

    按照用户要求的新流程：
    1. PDF → GROBID转文本（使用现有解析器）
    2. 按章节划分（Abstract/Introduction/Methods/Results/Discussion/Conclusion）
    3. Skill作为system prompt，论文文本作为input data
    4. 严格按照8维度分析每个章节
    5. 输出各章节详细md文件

    Args:
        papers_dir: 论文目录
        output_dir: 输出目录
        journal_name: 期刊名称
        deepseek_api_key: DeepSeek API密钥

    Returns:
        Dict[str, str]: 生成的文件路径字典
    """
    from analyzer.journal_style_analyzer import JournalStyleAnalyzer

    # 初始化DeepSeek分析器
    deepseek_analyzer = AIDeepSeekAnalyzer(deepseek_api_key)

    # 加载skill定义文件（将作为system prompt）
    skill_content = deepseek_analyzer.load_skill_definition()

    print(f"Loaded skill definition: {len(skill_content)} characters")

    # 获取papers_dir中的所有文件
    if os.path.isdir(papers_dir):
        paper_files = [
            os.path.join(papers_dir, f)
            for f in os.listdir(papers_dir)
            if f.endswith((".pdf", ".md", ".txt"))
        ]
    else:
        paper_files = [papers_dir]

    # 为每个章节收集所有样本
    all_sections = {
        "abstract": [],
        "introduction": [],
        "methods": [],
        "results": [],
        "discussion": [],
        "conclusion": [],
    }

    # 处理每篇论文
    for paper_file in paper_files[:10]:  # 限制处理前10个文件
        try:
            print(f"Processing: {paper_file}")

            # 提取章节文本（使用现有解析器，相当于GROBID的功能）
            analyzer = JournalStyleAnalyzer()
            sections = analyzer.extract_text_from_pdf(Path(paper_file))

            # 收集到对应章节
            for section_name, text in sections.items():
                section_key = section_name.lower().strip()
                if section_key in all_sections:
                    all_sections[section_key].append(text)
                    print(f"  Added {section_name}: {len(text)} chars")
                else:
                    # 处理变体名称
                    if "abstract" in section_key:
                        all_sections["abstract"].append(text)
                    elif "intro" in section_key:
                        all_sections["introduction"].append(text)
                    elif "method" in section_key:
                        all_sections["methods"].append(text)
                    elif "result" in section_key:
                        all_sections["results"].append(text)
                    elif "disc" in section_key:
                        all_sections["discussion"].append(text)
                    elif "concl" in section_key:
                        all_sections["conclusion"].append(text)

        except Exception as e:
            print(f"Failed to process {paper_file}: {e}")
            continue

    # 创建输出目录
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # 为每个章节生成详细分析
    section_guides = {}

    for section_name, samples in all_sections.items():
        if not samples:
            print(f"Skipping {section_name}: no samples")
            continue

        print(f"\n{'=' * 60}")
        print(f"Analyzing {section_name} section ({len(samples)} samples)")
        print(f"{'=' * 60}")

        try:
            # 调用DeepSeek进行8维度分析
            # 传入：skill (system) + 论文文本 (user)
            analysis_result = deepseek_analyzer.analyze_section_with_skill(
                section_samples=samples,
                section_name=section_name,
                journal_name=journal_name,
            )

            if not analysis_result:
                print(f"  Failed to get analysis for {section_name}")
                continue

            # 生成详细的章节md文件
            guide_content = _generate_detailed_section_guide(
                section_name=section_name,
                journal_name=journal_name,
                samples_count=len(samples),
                analysis_result=analysis_result,
                skill_content=skill_content,
            )

            # 保存到文件
            guide_path = Path(output_dir) / f"{section_name}_guide.md"
            with open(guide_path, "w", encoding="utf-8") as f:
                f.write(guide_content)

            section_guides[section_name] = str(guide_path)
            print(f"  Generated: {guide_path}")

            # 验证结果包含8个维度
            required_dimensions = [
                "function",
                "role_in_paper",
                "information_structure",
                "information_density",
                "stance_hedging",
                "sentence_pattern_functions",
                "lexical_features_by_pos",
                "constraints_and_avoidances",
            ]

            missing = [d for d in required_dimensions if d not in analysis_result]
            if missing:
                print(f"  Warning: Missing dimensions: {missing}")
            else:
                print(f"  Success: All 8 dimensions present")

        except Exception as e:
            print(f"Failed to analyze {section_name}: {e}")
            import traceback

            traceback.print_exc()
            continue

    # 生成汇总文件
    summary_content = _generate_summary_markdown(journal_name, section_guides)
    summary_path = Path(output_dir) / "style_summary.md"
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write(summary_content)

    print(f"\n{'=' * 60}")
    print("Analysis Complete!")
    print(f"{'=' * 60}")
    print(f"Generated {len(section_guides)} section guides")

    return {
        "report": str(summary_path),
        "summary": str(summary_path),
        "guides": section_guides,
    }


def _generate_detailed_section_guide(
    section_name: str,
    journal_name: str,
    samples_count: int,
    analysis_result: Dict[str, Any],
    skill_content: str,
) -> str:
    """生成详细的章节指南，严格按照8维度格式"""

    # 提取各维度数据
    function_data = analysis_result.get("function", {})
    role_data = analysis_result.get("role_in_paper", {})
    structure_data = analysis_result.get("information_structure", {})
    density_data = analysis_result.get("information_density", {})
    stance_data = analysis_result.get("stance_hedging", {})
    patterns_data = analysis_result.get("sentence_pattern_functions", [])
    lexical_data = analysis_result.get("lexical_features_by_pos", {})
    constraints_data = analysis_result.get("constraints_and_avoidances", {})

    # 构建指南内容
    guide = f"""# {section_name.title()} Writing Guide for {journal_name}

## Overview
- **Analyzed samples**: {samples_count}
- **Analysis based on**: {journal_name} journal style requirements
- **Framework**: 8-Dimension Style Analysis (per journal_section_style_skill.md)

---

## 1. Function (Communicative Goals)

**Requirements** (Must + action + object):
"""

    # 添加function requirements
    requirements = function_data.get("requirements", [])
    if isinstance(requirements, list):
        for req in requirements:
            guide += f"- {req}\n"
    else:
        guide += f"- {requirements}\n"

    communicative_goals = function_data.get("communicative_goals", "")
    guide += f"""
**Communicative Goals**: {communicative_goals}

---

## 2. Role in the Paper

**Description**:
{role_data.get("description", "Not specified")}

**Contribution Type**: {role_data.get("contribution_type", "Not specified")}

---

## 3. Information Structure (Rhetorical Moves)

**Stepwise Path**:
"""

    # 添加rhetorical moves
    moves = structure_data.get("rhetorical_moves", [])
    if isinstance(moves, list):
        for move in moves:
            guide += f"- {move}\n"
    else:
        guide += f"- {moves}\n"

    guide += f"""
**Flow Description**: {structure_data.get("flow_description", "Not specified")}

---

## 4. Information Density

- **High Detail**: {density_data.get("high_detail", "Not specified")}
- **Low Detail**: {density_data.get("low_detail", "Not specified")}
- **Typical Range**: {density_data.get("typical_range", "Not specified")}

---

## 5. Stance & Hedging (Allowed Intensity Band)

- **Intensity Band**: {stance_data.get("intensity_band", "Not specified")}
- **Author Voice**: {stance_data.get("author_voice", "Not specified")}
- **Claim Strength**: {stance_data.get("claim_strength", "Not specified")}
- **Certainty Level**: {stance_data.get("certainty_level", "Not specified")}

---

## 6. Sentence-Pattern Functions (Exactly 6 Categories)

"""

    # 添加sentence patterns（正好6个）
    for i, pattern in enumerate(patterns_data[:6], 1):
        guide += f"""### {i}. {pattern.get("function", "Unknown Function")}
- **Typical Position**: {pattern.get("typical_position", "Not specified")}
- **Journal Preference**: {pattern.get("journal_preference", "Not specified")}

"""

    guide += """## 7. Lexical Features by POS (Top 35 Words - Stop Words Excluded)

"""

    # 添加lexical features for each POS
    pos_order = ["nouns", "verbs", "adjectives", "adverbs"]
    pos_titles = ["Nouns", "Verbs", "Adjectives", "Adverbs"]

    for pos, title in zip(pos_order, pos_titles):
        if pos in lexical_data:
            features = lexical_data[pos]
            guide += f"""### {title}
"""
            # 添加top 35词汇
            top_words = features.get("top_35", [])
            if top_words and isinstance(top_words, list) and len(top_words) > 0:
                guide += f"**Top 35 Words**: {', '.join(top_words[:35])}\n\n"

            guide += f"""- **Semantic Orientation**: {features.get("semantic_orientation", "Not specified")}
- **Refer To**: {features.get("refer_to", "Not specified")}
- **Intensify/Soften/Neutral**: {features.get("intensify_soften_neutral", "Not specified")}
- **Profile Summary**: {features.get("profile_summary", "Not specified")}

"""

    guide += """## 8. Constraints & Avoidances (Do/Don't List)

### Do:
"""

    # 添加Do list
    do_list = constraints_data.get("do", [])
    if isinstance(do_list, list):
        for do in do_list:
            guide += f"- {do}\n"
    else:
        guide += f"- {do_list}\n"

    guide += """
### Don't:
"""

    # 添加Don't list
    dont_list = constraints_data.get("dont", [])
    if isinstance(dont_list, list):
        for dont in dont_list:
            guide += f"- {dont}\n"
    else:
        guide += f"- {dont_list}\n"

    boundary_rules = constraints_data.get("boundary_rules", "")
    if boundary_rules:
        guide += f"""
### Boundary Rules
{boundary_rules}

"""

    guide += (
        """---

## Quick Reference Card

| Dimension | Key Points |
|-----------|------------|
| Function | """
        + ", ".join(
            [
                r.strip()
                for r in (
                    requirements if isinstance(requirements, list) else [requirements]
                )
            ][:3]
        )
        + """ |
| Role | """
        + role_data.get("contribution_type", "N/A")
        + """ |
| Structure | """
        + str(len(moves))
        + """ rhetorical moves |
| Density | """
        + stance_data.get("intensity_band", "N/A")
        + """ |
| Stance | """
        + stance_data.get("certainty_level", "N/A")
        + """ |
| Patterns | 6 sentence functions |
| Lexical | Nouns/Verbs/Adjectives/Adverbs |
| Constraints | """
        + str(len(do_list))
        + """ Do's, """
        + str(len(dont_list))
        + """ Don'ts |

---

*Generated based on {samples_count} sample papers from {journal_name}*
*Following journal_section_style_skill.md framework*
"""
    )

    return guide


def _generate_summary_markdown(
    journal_name: str, section_guides: Dict[str, str]
) -> str:
    """生成汇总markdown"""

    guide = f"""# {journal_name} Style Analysis Summary

## Overview
This style analysis was generated using AI-enhanced analysis based on the **8-Dimension Style Framework** from `journal_section_style_skill.md`.

## Generated Section Guides

| Section | Status | File |
|---------|--------|------|
"""

    for section_name, guide_path in section_guides.items():
        guide += f"| {section_name.title()} | ✅ Generated | [View]({os.path.basename(guide_path)}) |\n"

    guide += """
## Analysis Framework (8 Dimensions)

1. **Function** - Communicative goals (3-5 hard requirements)
2. **Role in the Paper** - Section contribution to overall argument
3. **Information Structure** - Rhetorical moves with mandatory/optional
4. **Information Density** - Detail level range
5. **Stance & Hedging** - Confidence and caution balance
6. **Sentence-Pattern Functions** - Exactly 6 categories
7. **Lexical Features by POS** - N/V/Adj/Adv analysis
8. **Constraints & Avoidances** - Do/Don't list

## Usage

Each section guide provides detailed instructions for writing that section according to the target journal's style. Use the "Quick Reference Card" at the end of each guide for fast lookup.

---

*Analysis generated using DeepSeek AI*
*Framework: journal_section_style_skill.md*
"""

    return guide


def generate_section_guide_from_analysis(
    analysis: Dict[str, Any], section_name: str, journal_name: str
) -> str:
    """根据skill标准的分析结果生成章节指南"""
    guide = f"""# {section_name.title()} Writing Guide for {journal_name}

## Overview
Analysis based on journal section style skill framework.

## 1. Function
"""

    # 添加各个维度
    for func in analysis.get("function", []):
        guide += f"- {func}\n"
    guide += "\n"

    guide += f"## 2. Role in the Paper\n{analysis.get('role', 'Not analyzed')}\n\n"

    guide += "## 3. Information Structure\n"
    for i, structure in enumerate(analysis.get("information_structure", []), 1):
        guide += f"{i}. {structure}\n"
    guide += "\n"

    # 添加其他维度
    density = analysis.get("information_density", {})
    guide += "## 4. Information Density\n"
    guide += f"- High detail: {density.get('high', 'Detailed analysis')}\n"
    guide += f"- Low detail: {density.get('low', 'Brief overview')}\n\n"

    hedging = analysis.get("stance_hedging", {})
    guide += "## 5. Stance & Hedging\n"
    guide += f"- Band: {hedging.get('band', 'Moderate')}\n"
    guide += f"- Presence: {hedging.get('presence', 'Professional')}\n\n"

    guide += "## 6. Sentence-Pattern Functions\n"
    for pattern in analysis.get("sentence_patterns", [])[:6]:
        func = pattern.get("function", "Unknown")
        pos = pattern.get("position", "Various")
        pref = pattern.get("preference", "Standard")
        guide += f"- **{func}**: {pos} - {pref}\n"
    guide += "\n"

    guide += "## 7. Lexical Features by POS\n"
    lexical = analysis.get("lexical_features", {})
    for pos, features in lexical.items():
        guide += f"### {pos.title()}\n"
        orientation = features.get("orientation", "Various")
        refer_to = features.get("refer_to", "Multiple")
        role = features.get("role", "Contextual")
        guide += f"- Orientation: {orientation}\n"
        guide += f"- Refers to: {refer_to}\n"
        guide += f"- Role: {role}\n\n"

    constraints = analysis.get("constraints", {})
    guide += "## 8. Constraints & Avoidances\n"
    guide += "### Do:\n"
    for do in constraints.get("do", []):
        guide += f"- {do}\n"

    guide += "\n### Don't:\n"
    for dont in constraints.get("dont", []):
        guide += f"- {dont}\n"

    return guide


def generate_comprehensive_summary(
    analyses: Dict[str, Dict[str, Any]], journal_name: str
) -> str:
    """生成综合风格摘要"""
    summary = f"""# {journal_name} Comprehensive Style Summary

## Analysis Overview
AI-powered 8-dimension style analysis based on journal section skill framework.

## Section Analysis Results
"""

    for section_name, analysis in analyses.items():
        summary += f"### {section_name.title()}\n"
        summary += f"- Functions identified: {len(analysis.get('function', []))}\n"
        summary += (
            f"- Sentence patterns: {len(analysis.get('sentence_patterns', []))}\n"
        )
        summary += f"- Lexical features analyzed: {len(analysis.get('lexical_features', {}))}\n\n"

    summary += """
## Analysis Framework
- **8 Dimensions**: Function, Role, Structure, Density, Stance, Patterns, Lexical, Constraints
- **Method**: DeepSeek AI with skill-based standardization
- **Output**: Section-specific writing guides and comprehensive reports
"""

    return summary


def generate_section_guide(style_card: SectionStyleCard) -> str:
    """根据风格卡片生成章节指南 - 严格按照skill的8维度要求"""
    guide = f"""# {style_card.section_name.title()} Writing Guide for {style_card.journal_name}

## Overview
Based on analysis of {style_card.sample_size} sample papers.

## 1. Function (Communicative Goals)
This section must accomplish the following tasks:
"""

    # 添加function requirements
    for func in style_card.dimensions.function:
        guide += f"- {func}\n"
    guide += "\n"

    guide += f"""## 2. Role in the Paper
{style_card.dimensions.role}

## 3. Information Structure (Rhetorical Moves)
"""

    # 添加information structure
    for structure in style_card.dimensions.information_structure:
        guide += f"{structure}\n"
    guide += "\n"

    # 添加information density
    high_detail = style_card.dimensions.information_density.get("high", "Not specified")
    low_detail = style_card.dimensions.information_density.get("low", "Not specified")
    typical_range = style_card.dimensions.information_density.get(
        "typical_range", "Not specified"
    )

    guide += f"""## 4. Information Density
- **High Detail**: {high_detail}
- **Low Detail**: {low_detail}
- **Typical Range**: {typical_range}

## 5. Stance & Hedging (Allowed Intensity Band)
"""

    # 添加stance & hedging
    stance_data = style_card.dimensions.stance_hedging
    guide += f"""- **Intensity Band**: {stance_data.get("band", "Not specified")}
- **Author Voice**: {stance_data.get("presence", "Not specified")}
- **Claim Strength**: {stance_data.get("claim_strength", "Not specified")}
- **Certainty Level**: {stance_data.get("certainty_level", "Not specified")}

## 6. Sentence-Pattern Functions (Exactly 6 Categories)
"""

    # 添加sentence patterns (正好6个)
    for i, pattern in enumerate(style_card.dimensions.sentence_patterns[:6], 1):
        function_desc = pattern.get("function", "Unknown function")
        position = pattern.get("typical_position", "Not specified")
        preference = pattern.get("journal_preference", "Not specified")
        guide += f"{i}. **Function**: {function_desc}\n"
        guide += f"   - **Typical Position**: {position}\n"
        guide += f"   - **Journal Preference**: {preference}\n\n"

    guide += "## 7. Lexical Features by POS (Top-40 Feature Summary)\n"

    # 添加lexical features for each POS
    for pos in ["nouns", "verbs", "adjectives", "adverbs"]:
        if pos in style_card.dimensions.lexical_features:
            features = style_card.dimensions.lexical_features[pos]
            guide += f"### {pos.title()}\n"
            guide += f"- **Semantic Orientation**: {features.get('semantic_orientation', 'Not specified')}\n"
            guide += f"- **Refer To**: {features.get('refer_to', 'Not specified')}\n"
            guide += f"- **Intensify/Soften/Neutral**: {features.get('intensify_soften_neutral', 'Not specified')}\n"
            guide += f"- **Profile Summary**: {features.get('profile_summary', 'Not specified')}\n\n"

    # 添加constraints & avoidances
    constraints = style_card.dimensions.constraints
    guide += "## 8. Constraints & Avoidances (Do/Don't List)\n"

    guide += "### Do:\n"
    for do in constraints.get("do", []):
        guide += f"- {do}\n"

    guide += "\n### Don't:\n"
    for dont in constraints.get("dont", []):
        guide += f"- {dont}\n"

    boundary_rules = constraints.get("boundary_rules", "Not specified")
    if boundary_rules and boundary_rules != "Not specified":
        guide += f"\n### Boundary Rules:\n{boundary_rules}\n"

    guide += "\n### Don't:\n"
    for dont in constraints.get("dont", []):
        guide += f"- {dont}\n"

    return guide


def generate_style_summary(
    style_cards: Dict[str, SectionStyleCard], journal_name: str
) -> str:
    """生成综合风格摘要"""
    summary = f"""# {journal_name} Style Summary

## Overview
AI-enhanced style analysis based on journal section samples.

## Section Analysis
"""

    for section_name, card in style_cards.items():
        summary += f"### {section_name.title()}\n"
        summary += f"- Sample size: {card.sample_size}\n"
        summary += f"- Key functions: {len(card.dimensions.function)}\n"
        summary += f"- Sentence patterns: {len(card.dimensions.sentence_patterns)}\n\n"

    summary += """
## Analysis Method
- AI-powered 8-dimension analysis using DeepSeek
- RAG-enhanced feature extraction
- Based on journal section style skill definition
"""

    return summary
