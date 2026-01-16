#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试修复后的AI风格分析器，确保输出符合skill要求
"""

import sys
import os
import json
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))


def test_section_style_card_format():
    """测试Section Style Card格式"""
    print("测试Section Style Card格式...")

    try:
        from src.analyzer.ai_deepseek_analyzer import AIDeepSeekAnalyzer

        # 创建分析器实例
        analyzer = AIDeepSeekAnalyzer(
            api_key="sk-449b01267f914325877a6cedf054a481",
            base_url="http://127.0.0.1:13148/v1",
        )

        # 模拟测试数据
        test_samples = [
            """Introduction: This study investigates the effects of climate change on biodiversity. 
            Climate change has become one of the most pressing issues of our time, affecting ecosystems worldwide. 
            Previous research has shown significant impacts on various species, but gaps remain in our understanding. 
            The objective of this study is to address these gaps and provide comprehensive analysis.""",
            """Introduction: Climate change represents a significant threat to global biodiversity. 
            Numerous studies have documented changes in species distribution and abundance. 
            However, the long-term implications remain unclear. 
            This research aims to clarify these implications through systematic analysis.""",
            """Introduction: The relationship between climate change and biodiversity requires urgent investigation. 
            Current evidence suggests complex interactions between environmental factors and species responses. 
            While progress has been made, critical knowledge gaps persist. 
            Our study seeks to fill these gaps using innovative methodologies.""",
            """Introduction: Understanding climate change impacts on biodiversity is essential for conservation efforts. 
            Research has demonstrated various patterns of species response to environmental changes. 
            Nevertheless, comprehensive synthesis is lacking. 
            This paper contributes to filling this important knowledge gap.""",
            """Introduction: Climate change effects on biodiversity represent a critical research priority. 
            Existing literature provides valuable insights but remains fragmented. 
            The need for integrated analysis is evident. 
            Our study addresses this need through comprehensive examination of available data.""",
        ]

        # 测试分析
        result = analyzer.analyze_section_with_skill(
            section_samples=test_samples,
            section_name="introduction",
            journal_name="Nature Communications",
        )

        if result:
            print("分析成功完成")

            # 验证结构
            required_fields = [
                "function",
                "role_in_paper",
                "information_structure",
                "information_density",
                "stance_hedging",
                "sentence_pattern_functions",
                "lexical_features_by_pos",
                "constraints_and_avoidances",
            ]

            missing_fields = [field for field in required_fields if field not in result]
            if missing_fields:
                print(f"缺少字段: {missing_fields}")
                return False

            # 验证sentence patterns数量
            if len(result["sentence_pattern_functions"]) != 6:
                print(
                    f"Sentence patterns数量错误: {len(result['sentence_pattern_functions'])}, 期望6"
                )
                return False

            # 验证lexical features
            pos_types = ["nouns", "verbs", "adjectives", "adverbs"]
            for pos in pos_types:
                if pos not in result["lexical_features_by_pos"]:
                    print(f"缺少lexical features: {pos}")
                    return False

            print("所有格式验证通过")

            # 保存结果用于检查
            output_file = project_root / "test_section_style_card_output.json"
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            print(f"结果已保存到: {output_file}")

            return True
        else:
            print("分析失败，返回空结果")
            return False

    except Exception as e:
        print(f"测试失败: {e}")
        return False


def test_skill_file_loading():
    """测试skill文件加载"""
    print("测试skill文件加载...")

    try:
        from src.analyzer.ai_deepseek_analyzer import AIDeepSeekAnalyzer

        analyzer = AIDeepSeekAnalyzer(
            api_key="sk-449b01267f914325877a6cedf054a481",
            base_url="http://127.0.0.1:13148/v1",
        )
        skill_content = analyzer.load_skill_definition()

        if skill_content and len(skill_content) > 1000:
            print("Skill文件加载成功")
            print(f"文件长度: {len(skill_content)} 字符")

            # 检查关键内容
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
        print(f"测试失败: {e}")
        return False


def main():
    """主测试函数"""
    print("开始测试修复后的AI风格分析器")
    print("=" * 50)

    # 测试1: Skill文件加载
    test1_result = test_skill_file_loading()
    print()

    # 测试2: Section Style Card格式
    test2_result = test_section_style_card_format()
    print()

    # 总结
    print("=" * 50)
    if test1_result and test2_result:
        print("所有测试通过！修复成功")
        print("现在风格提取应该严格按照skill的8维度要求输出")
    else:
        print("部分测试失败，需要进一步调试")

    return test1_result and test2_result


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
