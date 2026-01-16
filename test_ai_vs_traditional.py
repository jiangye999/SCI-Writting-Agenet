#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试AI增强分析是否正确工作
"""

import sys
import os
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))


def test_ai_vs_traditional():
    """对比AI增强分析和传统分析的区别"""
    print("测试AI增强分析 vs 传统分析")
    print("=" * 50)

    try:
        # 1. 测试传统分析
        print("1. 测试传统分析...")
        from src.analyzer.journal_style_analyzer import JournalStyleAnalyzer

        traditional_analyzer = JournalStyleAnalyzer("english")
        traditional_result = traditional_analyzer.analyze_text(
            "This is a test abstract. We investigated the effects of climate change on biodiversity. "
            "Our findings suggest significant impacts. These results contribute to understanding.",
            "abstract",
        )

        print(f"传统分析结果类型: {type(traditional_result)}")
        print(f"传统分析键: {list(traditional_result.keys())}")

        # 2. 测试AI增强分析（如果API可用）
        print("\n2. 测试AI增强分析...")

        # 检查skill文件是否存在
        skill_file = (
            r"E:\AI_projects\学术写作\paper_writer\journal_section_style_skill.md"
        )
        if os.path.exists(skill_file):
            print("✓ Skill文件存在，应该使用AI增强分析")

            # 模拟AI分析结果
            mock_ai_result = {
                "function": {
                    "requirements": [
                        "Must establish research context",
                        "Must identify knowledge gap",
                        "Must state objectives",
                    ]
                },
                "role_in_paper": {
                    "description": "The abstract provides concise overview of the study"
                },
                "information_structure": {
                    "rhetorical_moves": [
                        "1. Background context (mandatory)",
                        "2. Study purpose (mandatory)",
                        "3. Key findings (mandatory)",
                        "4. Implications (optional)",
                    ]
                },
                "sentence_pattern_functions": [
                    {
                        "function": "Context establishment",
                        "typical_position": "opening",
                    },
                    {"function": "Finding presentation", "typical_position": "middle"},
                    {"function": "Implication statement", "typical_position": "end"},
                ],
            }

            print("AI增强分析将输出8维度结构:")
            for key, value in mock_ai_result.items():
                print(f"  {key}: {type(value)} - {len(str(value))} 字符")

        else:
            print("✗ Skill文件不存在，使用传统分析")

        # 3. 检查问题所在
        print("\n3. 问题分析:")
        print("用户看到的问题:")
        print("- 平均句子长度: 0.0 words")
        print("- 被动语态比例: 0%")
        print("- 结构是简单模板，不是8维度")

        print("\n可能原因:")
        print("1. 数据合并问题 - chunked分析返回空数据")
        print("2. app.py调用了错误的函数")
        print("3. 模板覆盖了真正的分析结果")

        # 4. 检查app.py逻辑
        print("\n4. 检查app.py中的调用逻辑...")

        app_file = project_root / "app.py"
        if app_file.exists():
            app_content = app_file.read_text(encoding="utf-8")

            if "analyze_journal_style_with_ai" in app_content:
                print("✓ app.py包含AI增强分析调用")
            else:
                print("✗ app.py不包含AI增强分析调用")

            if "analyze_journal_style" in app_content:
                print("✓ app.py包含传统分析调用")
            else:
                print("✗ app.py不包含传统分析调用")

        return True

    except Exception as e:
        print(f"测试失败: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """主函数"""
    test_result = test_ai_vs_traditional()

    print("\n" + "=" * 50)
    if test_result:
        print("测试完成")
        print("\n建议解决方案:")
        print("1. 确保使用AI增强分析而不是传统分析")
        print("2. 修复数据合并问题，避免返回空结果")
        print("3. 确保输出是8维度格式，不是简单模板")
        print("4. 在app中正确显示AI分析结果")
    else:
        print("测试失败")

    return test_result


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
