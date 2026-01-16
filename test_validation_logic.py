#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模拟测试AI风格分析器的输出格式验证
"""

import sys
import json
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))


def test_validation_logic():
    """测试验证逻辑"""
    print("测试验证逻辑...")

    try:
        from src.analyzer.ai_deepseek_analyzer import AIDeepSeekAnalyzer

        analyzer = AIDeepSeekAnalyzer(api_key="test-key", base_url="http://test-url")

        # 模拟正确的Section Style Card
        correct_result = {
            "section_name": "introduction",
            "journal": "Nature Communications",
            "sample_count": 5,
            "function": {
                "requirements": [
                    "Must establish research context",
                    "Must identify knowledge gap",
                    "Must state objectives",
                ],
                "communicative_goals": "Brief description",
            },
            "role_in_paper": {
                "description": "1 short paragraph defining contribution",
                "contribution_type": "setup",
            },
            "information_structure": {
                "rhetorical_moves": [
                    "1. Context (mandatory)",
                    "2. Problem (mandatory)",
                    "3. Literature (optional)",
                ],
                "flow_description": "Stepwise path",
            },
            "information_density": {
                "high_detail": "Detailed analysis",
                "low_detail": "Brief summary",
                "typical_range": "Medium to high",
            },
            "stance_hedging": {
                "intensity_band": "moderately assertive",
                "author_voice": "impersonal tone",
                "claim_strength": "qualified claims",
                "certainty_level": "Medium certainty",
            },
            "sentence_pattern_functions": [
                {
                    "function": "Context establishment",
                    "typical_position": "paragraph start",
                    "journal_preference": "journal-specific",
                },
                {
                    "function": "Gap identification",
                    "typical_position": "paragraph middle",
                    "journal_preference": "general academic",
                },
                {
                    "function": "Purpose statement",
                    "typical_position": "paragraph end",
                    "journal_preference": "journal-specific",
                },
                {
                    "function": "Literature synthesis",
                    "typical_position": "throughout",
                    "journal_preference": "general academic",
                },
                {
                    "function": "Significance claim",
                    "typical_position": "final paragraph",
                    "journal_preference": "journal-specific",
                },
                {
                    "function": "Future work preview",
                    "typical_position": "optional closing",
                    "journal_preference": "general academic",
                },
            ],
            "lexical_features_by_pos": {
                "nouns": {
                    "semantic_orientation": "abstract/technical",
                    "refer_to": "concepts",
                    "intensify_soften_neutral": "neutral",
                    "profile_summary": "Abstract concepts",
                },
                "verbs": {
                    "semantic_orientation": "investigative",
                    "refer_to": "actions",
                    "intensify_soften_neutral": "neutral",
                    "profile_summary": "Action verbs",
                },
                "adjectives": {
                    "semantic_orientation": "evaluative",
                    "refer_to": "quality",
                    "intensify_soften_neutral": "qualifying",
                    "profile_summary": "Evaluative terms",
                },
                "adverbs": {
                    "semantic_orientation": "hedging",
                    "refer_to": "certainty",
                    "intensify_soften_neutral": "softening",
                    "profile_summary": "Hedging terms",
                },
            },
            "constraints_and_avoidances": {
                "do": [
                    "Use formal language",
                    "Cite literature",
                    "Maintain objectivity",
                ],
                "dont": [
                    "Avoid claims without evidence",
                    "Avoid personal opinions",
                    "Avoid informal language",
                ],
                "boundary_rules": "No method details in introduction",
            },
        }

        # 测试验证函数
        validation_result = analyzer._validate_section_style_card(correct_result)

if validation_result:
            print("正确格式的验证通过")
        else:
            print("正确格式的验证失败")
            return False
        
        # 测试错误的格式（缺少sentence pattern）
        incorrect_result = correct_result.copy()
        incorrect_result["sentence_pattern_functions"] = [
            {"function": "only one pattern"}
        ]  # 只有1个，不是6个
        
        validation_result2 = analyzer._validate_section_style_card(incorrect_result)
        
        if not validation_result2:
            print("错误格式的验证正确拒绝")
        else:
            print("错误格式的验证应该失败但通过了")
            return False
        
        print("所有验证逻辑测试通过")
        return True

    except Exception as e:
        print(f"❌ 验证逻辑测试失败: {e}")
        return False


def test_skill_file_loading():
    """测试skill文件加载"""
    print("测试skill文件加载...")

    try:
        from src.analyzer.ai_deepseek_analyzer import AIDeepSeekAnalyzer

        analyzer = AIDeepSeekAnalyzer(api_key="test-key", base_url="http://test-url")

        skill_content = analyzer.load_skill_definition()

if skill_content and len(skill_content) > 1000:
            print("Skill文件加载成功")
            print(f"文件长度: {len(skill_content)} 字符")
            
            # 检查关键内容
            if "8-Dimension Template" in skill_content and "Section Style Card" in skill_content:
                print("Skill文件内容验证通过")
                return True
            else:
                print("Skill文件内容不完整")
                return False
        else:
            print("Skill文件加载失败")
            return False
            
    except Exception as e:
        print(f"Skill文件测试失败: {e}")
        return False


def main():
    """主测试函数"""
    print("开始模拟测试AI风格分析器")
    print("=" * 50)

    # 测试1: Skill文件加载
    test1_result = test_skill_file_loading()
    print()

    # 测试2: 验证逻辑
    test2_result = test_validation_logic()
    print()

    # 总结
    print("=" * 50)
    if test1_result and test2_result:
        print("✅ 所有模拟测试通过！")
        print("📋 核心逻辑修复完成")
        print("📋 风格提取现在严格按照skill的8维度要求验证")
        print("📋 需要API服务器运行才能进行完整测试")
    else:
        print("❌ 部分测试失败")

    return test1_result and test2_result


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
