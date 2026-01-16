#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化测试AI风格分析器的验证逻辑
"""

import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))


def test_skill_file_loading():
    """测试skill文件加载"""
    print("测试skill文件加载...")

    try:
        from src.analyzer.ai_deepseek_analyzer import AIDeepSeekAnalyzer

        analyzer = AIDeepSeekAnalyzer(api_key="test", base_url="http://test")
        skill_content = analyzer.load_skill_definition()

        if skill_content and len(skill_content) > 1000:
            print("Skill文件加载成功")
            print(f"文件长度: {len(skill_content)} 字符")

            if (
                "8-Dimension Template" in skill_content
                and "Section Style Card" in skill_content
            ):
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


def test_validation_logic():
    """测试验证逻辑"""
    print("测试验证逻辑...")

    try:
        from src.analyzer.ai_deepseek_analyzer import AIDeepSeekAnalyzer

        analyzer = AIDeepSeekAnalyzer(api_key="test", base_url="http://test")

        # 正确格式
        correct_result = {
            "function": {"requirements": ["Must do 1", "Must do 2", "Must do 3"]},
            "role_in_paper": {"description": "test role"},
            "information_structure": {"rhetorical_moves": ["move 1", "move 2"]},
            "information_density": {"high_detail": "test"},
            "stance_hedging": {"intensity_band": "test"},
            "sentence_pattern_functions": [
                {"function": "f1"},
                {"function": "f2"},
                {"function": "f3"},
                {"function": "f4"},
                {"function": "f5"},
                {"function": "f6"},
            ],
            "lexical_features_by_pos": {
                "nouns": {"test": "test"},
                "verbs": {"test": "test"},
                "adjectives": {"test": "test"},
                "adverbs": {"test": "test"},
            },
            "constraints_and_avoidances": {"do": ["do1"], "dont": ["dont1"]},
        }

        # 测试正确格式
        if analyzer._validate_section_style_card(correct_result):
            print("正确格式的验证通过")
        else:
            print("正确格式的验证失败")
            return False

        # 测试错误格式（只有3个sentence pattern）
        incorrect_result = correct_result.copy()
        incorrect_result["sentence_pattern_functions"] = [{"function": "f1"}]

        if not analyzer._validate_section_style_card(incorrect_result):
            print("错误格式的验证正确拒绝")
        else:
            print("错误格式的验证应该失败但通过了")
            return False

        print("所有验证逻辑测试通过")
        return True

    except Exception as e:
        print(f"验证逻辑测试失败: {e}")
        return False


def main():
    """主测试函数"""
    print("开始模拟测试AI风格分析器")
    print("=" * 50)

    test1_result = test_skill_file_loading()
    print()

    test2_result = test_validation_logic()
    print()

    print("=" * 50)
    if test1_result and test2_result:
        print("所有模拟测试通过！")
        print("核心逻辑修复完成")
        print("风格提取现在严格按照skill的8维度要求验证")
    else:
        print("部分测试失败")

    return test1_result and test2_result


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
