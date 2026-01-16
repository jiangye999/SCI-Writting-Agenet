#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试修复后的风格指南生成，确保严格按照skill的8维度要求
"""

import sys
import json
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))


def test_guide_generation():
    """测试修复后的指南生成"""
    print("测试修复后的指南生成...")

    try:
        from src.analyzer.ai_deepseek_analyzer import (
            generate_section_guide,
            SectionStyleCard,
            StyleDimension,
        )

        # 模拟符合新JSON结构的分析结果
        mock_analysis_result = {
            "section_name": "discussion",
            "journal": "Global Change Biology",
            "sample_count": 5,
            "function": {
                "requirements": [
                    "Must interpret principal findings",
                    "Must compare with existing literature",
                    "Must explain implications",
                    "Must acknowledge limitations",
                ],
                "communicative_goals": "Interpret results and explain significance",
            },
            "role_in_paper": {
                "description": "The discussion section interprets findings and explains their significance in the broader context of existing research.",
                "contribution_type": "interpretation",
            },
            "information_structure": {
                "rhetorical_moves": [
                    "1. Principal findings summary (mandatory)",
                    "2. Comparison with literature (mandatory)",
                    "3. Implications explanation (mandatory)",
                    "4. Limitations acknowledgment (mandatory)",
                    "5. Future directions (optional)",
                ],
                "flow_description": "From specific results to broader implications",
            },
            "information_density": {
                "high_detail": "Detailed interpretation of complex relationships",
                "low_detail": "Brief summary of key implications",
                "typical_range": "Moderate to high detail for interpretations",
            },
            "stance_hedging": {
                "intensity_band": "Balanced confidence and caution",
                "author_voice": "Professional but present",
                "claim_strength": "Qualified claims with appropriate hedging",
                "certainty_level": "Moderate certainty with appropriate caution",
            },
            "sentence_pattern_functions": [
                {
                    "function": "Principal findings summary",
                    "typical_position": "opening paragraphs",
                    "journal_preference": "journal-specific",
                },
                {
                    "function": "Literature comparison",
                    "typical_position": "middle paragraphs",
                    "journal_preference": "general academic",
                },
                {
                    "function": "Implication explanation",
                    "typical_position": "throughout",
                    "journal_preference": "journal-specific",
                },
                {
                    "function": "Limitation acknowledgment",
                    "typical_position": "penultimate paragraph",
                    "journal_preference": "general academic",
                },
                {
                    "function": "Future direction suggestion",
                    "typical_position": "final paragraph",
                    "journal_preference": "journal-specific",
                },
                {
                    "function": "Conclusion synthesis",
                    "typical_position": "throughout",
                    "journal_preference": "general academic",
                },
            ],
            "lexical_features_by_pos": {
                "nouns": {
                    "semantic_orientation": "abstract/technical",
                    "refer_to": "concepts, phenomena, relationships",
                    "intensify_soften_neutral": "neutral",
                    "profile_summary": "Technical terminology for scientific concepts",
                },
                "verbs": {
                    "semantic_orientation": "investigative",
                    "refer_to": "actions, processes, relationships",
                    "intensify_soften_neutral": "neutral to softening",
                    "profile_summary": "Analytical verbs for interpretation",
                },
                "adjectives": {
                    "semantic_orientation": "evaluative",
                    "refer_to": "quality assessments, significance",
                    "intensify_soften_neutral": "qualifying",
                    "profile_summary": "Evaluative terms for assessing findings",
                },
                "adverbs": {
                    "semantic_orientation": "hedging",
                    "refer_to": "certainty modifiers, intensity",
                    "intensify_soften_neutral": "softening",
                    "profile_summary": "Hedging terms for balanced claims",
                },
            },
            "constraints_and_avoidances": {
                "do": [
                    "Use balanced confidence and caution",
                    "Compare with relevant literature",
                    "Explain practical and theoretical implications",
                    "Acknowledge study limitations clearly",
                ],
                "dont": [
                    "Avoid overstating findings",
                    "Avoid ignoring contradictory evidence",
                    "Avoid excessive speculation",
                    "Avoid making unsupported claims",
                ],
                "boundary_rules": "Do not introduce new results in discussion",
            },
        }

        # 创建StyleDimension对象
        dimensions = StyleDimension(
            function=mock_analysis_result["function"]["requirements"],
            role=mock_analysis_result["role_in_paper"]["description"],
            information_structure=mock_analysis_result["information_structure"][
                "rhetorical_moves"
            ],
            information_density={
                "high": mock_analysis_result["information_density"]["high_detail"],
                "low": mock_analysis_result["information_density"]["low_detail"],
            },
            stance_hedging={
                "band": mock_analysis_result["stance_hedging"]["intensity_band"],
                "presence": mock_analysis_result["stance_hedging"]["author_voice"],
            },
            sentence_patterns=mock_analysis_result["sentence_pattern_functions"],
            lexical_features=mock_analysis_result["lexical_features_by_pos"],
            constraints=mock_analysis_result["constraints_and_avoidances"],
        )

        # 创建SectionStyleCard对象
        style_card = SectionStyleCard(
            section_name=mock_analysis_result["section_name"],
            journal_name=mock_analysis_result["journal"],
            analysis_date="2026-01-16",
            sample_size=mock_analysis_result["sample_count"],
            dimensions=dimensions,
        )

        # 生成指南
        guide = generate_section_guide(style_card)

        # 验证指南内容
        print("验证生成的指南内容...")

        # 检查8个维度是否都存在
        required_sections = [
            "## 1. Function (Communicative Goals)",
            "## 2. Role in the Paper",
            "## 3. Information Structure (Rhetorical Moves)",
            "## 4. Information Density",
            "## 5. Stance & Hedging (Allowed Intensity Band)",
            "## 6. Sentence-Pattern Functions (Exactly 6 Categories)",
            "## 7. Lexical Features by POS (Top-40 Feature Summary)",
            "## 8. Constraints & Avoidances (Do/Don't List)",
        ]

        missing_sections = []
        for section in required_sections:
            if section not in guide:
                missing_sections.append(section)

        if missing_sections:
            print(f"缺少的维度: {missing_sections}")
            return False
        else:
            print("所有8个维度都存在")

        # 检查具体内容
        content_checks = [
            ("Must interpret principal findings", "Function requirements"),
            ("The discussion section interprets findings", "Role description"),
            ("Principal findings summary (mandatory)", "Information structure"),
            ("High Detail:", "Information density"),
            ("Intensity Band:", "Stance & hedging"),
            ("Function:", "Sentence patterns"),
            ("### nouns", "Lexical features"),
            ("### Do:", "Constraints"),
        ]

        for check_text, description in content_checks:
            if check_text in guide:
                print(f"{description} 存在")
            else:
                print(f"{description} 缺失")
                return False

        # 保存生成的指南用于检查
        output_file = project_root / "test_fixed_discussion_guide.md"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(guide)
        print(f"生成的指南已保存到: {output_file}")

        print("指南生成测试通过")
        return True

    except Exception as e:
        print(f"指南生成测试失败: {e}")
        return False


def main():
    """主测试函数"""
    print("测试修复后的风格指南生成")
    print("=" * 50)

    test_result = test_guide_generation()

    print("=" * 50)
    if test_result:
        print("修复成功！")
        print("现在生成的指南将严格按照skill的8维度要求:")
        print("1. Function (3-5 hard requirements)")
        print("2. Role in the paper (1 short paragraph)")
        print("3. Information structure (stepwise path)")
        print("4. Information density (define the range)")
        print("5. Stance & hedging (allowed intensity band)")
        print("6. Sentence-pattern functions (exactly 6 categories)")
        print("7. Lexical features by POS (top-40 feature summary)")
        print("8. Constraints & avoidances (Do/Don't list)")
    else:
        print("修复失败，需要进一步调试")

    return test_result


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
