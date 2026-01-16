"""
草稿整合器模块
"""

import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml


@dataclass
class ConsistencyIssue:
    """一致性问题"""

    type: str  # 'numerical', 'terminology', 'citation', 'format'
    severity: str  # 'critical', 'warning', 'info'
    location: str  # e.g., "Results, paragraph 3"
    description: str
    original_value: str
    suggested_value: str
    auto_fixed: bool = False


@dataclass
class IntegrationReport:
    """整合报告"""

    integration_time: str = ""
    total_words: int = 0
    overall_quality_score: float = 0.0
    structure_analysis: Dict[str, Any] = None
    transition_analysis: Dict[str, Any] = None
    consistency_report: Dict[str, Any] = None
    issues_for_review: List[Dict] = None
    recommendations: List[str] = None

    def __post_init__(self):
        if self.structure_analysis is None:
            self.structure_analysis = {}
        if self.transition_analysis is None:
            self.transition_analysis = {}
        if self.consistency_report is None:
            self.consistency_report = {}
        if self.issues_for_review is None:
            self.issues_for_review = []
        if self.recommendations is None:
            self.recommendations = []


class DraftIntegrator:
    """草稿整合器"""

    # 过渡词分类
    TRANSITION_WORDS = {
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
            "afterwards",
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
        ],
    }

    def __init__(self, config_path: str = "config/config.yaml"):
        """
        初始化整合器

        Args:
            config_path: 配置文件路径
        """
        with open(config_path, "r") as f:
            self.config = yaml.safe_load(f)

        self.quality_thresholds = self.config.get("quality", {}).get("thresholds", {})

    def collect_sections(self, section_files: Dict[str, str]) -> Dict[str, str]:
        """
        收集各章节

        Args:
            section_files: 章节文件路径字典 {'introduction': 'path/to/intro.md', ...}

        Returns:
            章节内容字典
        """
        sections = {}
        for section_name, file_path in section_files.items():
            if Path(file_path).exists():
                sections[section_name] = Path(file_path).read_text(encoding="utf-8")
            else:
                print(f"警告: 找不到文件 {file_path}")
                sections[section_name] = ""

        return sections

    def validate_completeness(self, sections: Dict[str, str]) -> Dict[str, Any]:
        """
        验证完整性

        Args:
            sections: 章节内容字典

        Returns:
            验证报告
        """
        required_sections = ["introduction", "methods", "results", "discussion"]
        present_sections = [s for s in required_sections if sections.get(s, "").strip()]
        missing_sections = [
            s for s in required_sections if not sections.get(s, "").strip()
        ]

        # 计算字数
        word_counts = {s: len(sections.get(s, "").split()) for s in sections}
        total_words = sum(word_counts.values())

        return {
            "sections_present": present_sections,
            "sections_missing": missing_sections,
            "word_counts": word_counts,
            "total_words": total_words,
            "is_complete": len(missing_sections) == 0,
        }

    def check_data_consistency(
        self, sections: Dict[str, str], strict_mode: bool = False
    ) -> Tuple[List[ConsistencyIssue], Dict[str, Any]]:
        """
        检查数据一致性

        Args:
            sections: 章节内容字典
            strict_mode: 严格模式

        Returns:
            (问题列表, 统计信息)
        """
        issues = []
        stats = {
            "sample_size_mentions": [],
            "statistical_values": [],
            "terminology_occurrences": {},
        }

        # 提取样本量
        sample_pattern = r"n\s*[=:]\s*(\d+)"
        for section, content in sections.items():
            matches = re.findall(sample_pattern, content)
            if matches:
                stats["sample_size_mentions"].append(
                    {"section": section, "values": list(set(matches))}
                )

                # 检查是否一致
                unique_values = set(matches)
                if len(unique_values) > 1:
                    # 取最常见的值
                    most_common = max(set(matches), key=matches.count)
                    issues.append(
                        ConsistencyIssue(
                            type="numerical",
                            severity="critical" if strict_mode else "warning",
                            location=f"{section.capitalize()}",
                            description=f"样本量不一致: 发现了 {', '.join(unique_values)}",
                            original_value=", ".join(unique_values),
                            suggested_value=most_common,
                            auto_fixed=not strict_mode,
                        )
                    )

        # 提取统计值
        p_value_pattern = r"p\s*[<>=]\s*[\d.]+"
        for section, content in sections.items():
            matches = re.findall(p_value_pattern, content)
            if matches:
                stats["statistical_values"].append(
                    {
                        "section": section,
                        "values": matches[:5],  # 只保留前5个
                    }
                )

        # 提取术语使用
        # 检测潜在的术语不一致
        potential_terms = ["Table", "Figure"]
        for term in potential_terms:
            pattern = rf"{term}\s*\d+"
            for section, content in sections.items():
                matches = re.findall(pattern, content)
                if matches:
                    stats["terminology_occurrences"][term] = matches

        return issues, stats

    def check_terminology_consistency(
        self, sections: Dict[str, str]
    ) -> List[ConsistencyIssue]:
        """
        检查术语一致性

        Args:
            sections: 章节内容字典

        Returns:
            术语问题列表
        """
        issues = []

        # 检测常见的术语变体
        term_variants = {
            "crop yield": [
                "crop yield",
                "Crop yield",
                "crop yields",
                "Crop yields",
                "yields",
            ],
            "significant": [
                "significant",
                "Significant",
                "significantly",
                "Significantly",
            ],
            "control group": ["control group", "Control group", "control", "Control"],
            "treatment group": [
                "treatment group",
                "Treatment group",
                "treatment",
                "Treatment",
            ],
        }

        # 合并所有文本
        all_text = " ".join(sections.values()).lower()

        for standard_term, variants in term_variants.items():
            found_variants = [v for v in variants if v.lower() in all_text]
            if len(found_variants) > 1:
                issues.append(
                    ConsistencyIssue(
                        type="terminology",
                        severity="warning",
                        location="全文",
                        description=f"术语 '{standard_term}' 有多种变体",
                        original_value=", ".join(found_variants),
                        suggested_value=standard_term,
                        auto_fixed=True,
                    )
                )

        return issues

    def analyze_transitions(self, sections: Dict[str, str]) -> Dict[str, Any]:
        """
        分析过渡词

        Args:
            sections: 章节内容字典

        Returns:
            过渡分析结果
        """
        transition_counts = {k: 0 for k in self.TRANSITION_WORDS}

        for section, content in sections.items():
            content_lower = content.lower()
            for category, words in self.TRANSITION_WORDS.items():
                for word in words:
                    count = len(re.findall(r"\b" + word + r"\b", content_lower))
                    transition_counts[category] += count

        # 计算过渡密度
        total_words = sum(len(s.split()) for s in sections.values())
        total_transitions = sum(transition_counts.values())
        density = total_transitions / total_words if total_words > 0 else 0

        # 章节间过渡检查
        section_order = ["introduction", "methods", "results", "discussion"]
        section_transitions = {}

        for i, section in enumerate(section_order[:-1]):
            next_section = section_order[i + 1]
            if sections.get(section) and sections.get(next_section):
                # 检查前一章节最后一段是否有过渡到下一章节
                last_para = (
                    sections[section].strip().split("\n\n")[-1]
                    if sections[section].strip()
                    else ""
                )
                has_transition = any(
                    word in last_para.lower()
                    for word in [
                        "subsequently",
                        "therefore",
                        "these results",
                        "to examine",
                        "we then",
                    ]
                )
                section_transitions[f"{section}->{next_section}"] = has_transition

        return {
            "transition_counts": transition_counts,
            "total_transitions": total_transitions,
            "transition_density": round(density * 100, 2),
            "section_transitions": section_transitions,
            "transition_score": min(density * 50, 1.0),  # 简单评分
        }

    def improve_transitions(self, sections: Dict[str, str]) -> Dict[str, str]:
        """
        增强过渡词

        Args:
            sections: 章节内容字典

        Returns:
            增强后的章节
        """
        improved = sections.copy()

        # 章节间过渡
        section_transitions = {
            "introduction": "To investigate this question, we conducted",
            "methods": "The following methods were employed to address these objectives.",
            "results": "The results of these experiments are presented below.",
            "discussion": "These findings suggest that",
        }

        for section, transition in section_transitions.items():
            if improved.get(section):
                content = improved[section].strip()
                paragraphs = content.split("\n\n")
                if paragraphs:
                    # 在第一段添加过渡词
                    first_para = paragraphs[0]
                    if not any(
                        word in first_para.lower()
                        for word in ["however", "therefore", "furthermore"]
                    ):
                        paragraphs[0] = f"{transition} {first_para.lower()}"
                    improved[section] = "\n\n".join(paragraphs)

        return improved

    def auto_fix_consistency(
        self, sections: Dict[str, str], issues: List[ConsistencyIssue]
    ) -> Dict[str, str]:
        """
        自动修复一致性问题

        Args:
            sections: 章节内容字典
            issues: 问题列表

        Returns:
            修复后的章节
        """
        fixed = sections.copy()

        for issue in issues:
            if issue.auto_fixed and issue.type == "numerical":
                # 修复样本量不一致
                for section, content in fixed.items():
                    if (
                        issue.location.lower() in section.lower()
                        or "全文" in issue.location
                    ):
                        # 替换为建议值
                        fixed[section] = content.replace(
                            issue.original_value, issue.suggested_value
                        )

            elif issue.auto_fixed and issue.type == "terminology":
                # 修复术语不一致
                for section, content in fixed.items():
                    if (
                        "全文" in issue.location
                        or issue.location.lower() in section.lower()
                    ):
                        # 替换为标准术语
                        for variant in issue.original_value.split(", "):
                            if variant.strip():
                                fixed[section] = fixed[section].replace(
                                    variant.strip(), issue.suggested_value
                                )

        return fixed

    def integrate(
        self, sections: Dict[str, str], output_path: Optional[str] = None
    ) -> Tuple[str, IntegrationReport]:
        """
        整合所有章节

        Args:
            sections: 章节内容字典
            output_path: 输出文件路径

        Returns:
            (完整草稿, 整合报告)
        """
        report = IntegrationReport()
        report.integration_time = datetime.now().isoformat()

        # 1. 验证完整性
        completeness = self.validate_completeness(sections)
        report.structure_analysis = {
            "sections_present": completeness["sections_present"],
            "word_counts": completeness["word_counts"],
            "total_words": completeness["total_words"],
        }

        # 2. 检查数据一致性
        consistency_issues, consistency_stats = self.check_data_consistency(sections)
        terminology_issues = self.check_terminology_consistency(sections)

        all_issues = consistency_issues + terminology_issues

        # 自动修复
        fixed_sections = self.auto_fix_consistency(sections, all_issues)

        report.consistency_report = {
            "total_issues": len(all_issues),
            "critical": len([i for i in all_issues if i.severity == "critical"]),
            "warnings": len([i for i in all_issues if i.severity == "warning"]),
            "auto_fixed": len([i for i in all_issues if i.auto_fixed]),
        }

        # 3. 分析过渡词
        transition_analysis = self.analyze_transitions(fixed_sections)
        report.transition_analysis = transition_analysis

        # 4. 增强过渡词
        improved_sections = self.improve_transitions(fixed_sections)

        # 5. 生成完整草稿
        draft = self._assemble_draft(improved_sections)
        report.total_words = len(draft.split())

        # 6. 计算质量分数
        report.overall_quality_score = self._calculate_quality_score(report)

        # 7. 生成建议
        report.recommendations = self._generate_recommendations(report, all_issues)

        # 8. 保存问题清单
        report.issues_for_review = [
            {
                "type": issue.type,
                "severity": issue.severity,
                "location": issue.location,
                "description": issue.description,
                "suggested_value": issue.suggested_value,
            }
            for issue in all_issues
            if not issue.auto_fixed
        ]

        # 保存输出
        if output_path:
            Path(output_path).write_text(draft, encoding="utf-8")

        return draft, report

    def _assemble_draft(self, sections: Dict[str, str]) -> str:
        """
        组装完整草稿

        Args:
            sections: 章节内容字典

        Returns:
            完整草稿
        """
        # 按标准顺序组装
        section_order = ["introduction", "methods", "results", "discussion"]
        section_titles = {
            "introduction": "## Introduction",
            "methods": "## Methods",
            "results": "## Results",
            "discussion": "## Discussion",
        }

        draft_parts = []

        for section in section_order:
            content = sections.get(section, "").strip()
            if content:
                # 确保有标题
                if not content.startswith("## "):
                    draft_parts.append(
                        section_titles.get(section, f"## {section.capitalize()}")
                    )
                draft_parts.append(content)

        return "\n\n".join(draft_parts)

    def _calculate_quality_score(self, report: IntegrationReport) -> float:
        """
        计算质量分数

        Args:
            report: 整合报告

        Returns:
            质量分数 (0-1)
        """
        scores = {}

        # 结构完整性
        scores["structure"] = (
            1.0
            if len(report.structure_analysis.get("sections_present", [])) >= 4
            else 0.5
        )

        # 过渡质量
        scores["transitions"] = report.transition_analysis.get("transition_score", 0)

        # 一致性
        total_issues = report.consistency_report.get("total_issues", 0)
        critical = report.consistency_report.get("critical", 0)
        scores["consistency"] = max(0, 1.0 - (total_issues * 0.05) - (critical * 0.1))

        # 字数合理性
        total_words = report.total_words
        if 3000 < total_words < 8000:
            scores["length"] = 1.0
        elif 2000 < total_words < 10000:
            scores["length"] = 0.7
        else:
            scores["length"] = 0.5

        # 加权平均
        weights = {
            "structure": 0.2,
            "transitions": 0.25,
            "consistency": 0.30,
            "length": 0.25,
        }
        overall = sum(scores.get(k, 0) * v for k, v in weights.items())

        return round(overall, 2)

    def _generate_recommendations(
        self, report: IntegrationReport, issues: List[ConsistencyIssue]
    ) -> List[str]:
        """
        生成建议

        Args:
            report: 整合报告
            issues: 问题列表

        Returns:
            建议列表
        """
        recommendations = []

        if report.overall_quality_score < 0.8:
            recommendations.append("建议对全文进行人工审查和润色")

        if report.transition_analysis.get("transition_density", 0) < 1.5:
            recommendations.append("建议增加过渡词以改善章节间流畅度")

        critical_issues = [i for i in issues if i.severity == "critical"]
        if critical_issues:
            recommendations.append(
                f"存在 {len(critical_issues)} 个关键一致性问题需要审查"
            )

        if report.total_words < 3000:
            recommendations.append("文章较短，建议增加内容深度")
        elif report.total_words > 10000:
            recommendations.append("文章较长，建议精简内容")

        return recommendations

    def save_report(self, report: IntegrationReport, output_path: str) -> None:
        """
        保存报告

        Args:
            report: 整合报告
            output_path: 输出路径
        """
        report_dict = {
            "metadata": {
                "integration_time": report.integration_time,
                "total_words": report.total_words,
                "overall_quality_score": report.overall_quality_score,
            },
            "structure_analysis": report.structure_analysis,
            "transition_analysis": report.transition_analysis,
            "consistency_report": report.consistency_report,
            "issues_for_review": report.issues_for_review,
            "recommendations": report.recommendations,
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report_dict, f, ensure_ascii=False, indent=2)


def integrate_sections(
    section_files: Dict[str, str],
    output_path: str,
    config_path: str = "config/config.yaml",
) -> Tuple[str, Dict]:
    """
    整合章节的便捷函数

    Args:
        section_files: 章节文件路径字典
        output_path: 输出文件路径
        config_path: 配置文件路径

    Returns:
        (草稿路径, 报告字典)
    """
    integrator = DraftIntegrator(config_path)

    # 收集章节
    sections = integrator.collect_sections(section_files)

    # 整合
    draft, report = integrator.integrate(sections, output_path)

    # 保存报告
    report_path = output_path.replace(".md", "_report.json")
    integrator.save_report(report, report_path)

    return draft, {
        "draft_path": output_path,
        "report_path": report_path,
        "total_words": report.total_words,
        "quality_score": report.overall_quality_score,
        "issues_count": report.consistency_report.get("total_issues", 0),
    }


if __name__ == "__main__":
    import sys

    if len(sys.argv) >= 3:
        section_files = {
            "introduction": sys.argv[1],
            "methods": sys.argv[2],
            "results": sys.argv[3],
            "discussion": sys.argv[4] if len(sys.argv) > 4 else sys.argv[2],
        }
        output_path = sys.argv[5] if len(sys.argv) > 5 else "output/integrated_draft.md"

        draft, result = integrate_sections(section_files, output_path)
        print(f"整合完成!")
        print(f"草稿: {result['draft_path']}")
        print(f"字数: {result['total_words']}")
        print(f"质量分: {result['quality_score']}")
    else:
        print(
            "用法: python draft_integrator.py <引言文件> <方法文件> <结果文件> [讨论文件] [输出路径]"
        )
