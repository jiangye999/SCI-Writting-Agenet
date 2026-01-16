#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单测试指南生成，直接输出内容查看
"""

import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))


def test_simple():
    """简单测试"""
    try:
        from src.analyzer.ai_deepseek_analyzer import (
            generate_section_guide,
            SectionStyleCard,
            StyleDimension,
        )

        # 创建最简单的测试数据
        dimensions = StyleDimension(
            function=["Must do something", "Must do another"],
            role="Test role description",
            information_structure=["Step 1", "Step 2"],
            information_density={"high": "Test high", "low": "Test low"},
            stance_hedging={"band": "Test band", "presence": "Test presence"},
            sentence_patterns=[
                {
                    "function": "Test",
                    "typical_position": "Test",
                    "journal_preference": "Test",
                }
            ],
            lexical_features={"nouns": {"test": "test"}},
            constraints={"do": ["Test do"], "dont": ["Test dont"]},
        )

        style_card = SectionStyleCard(
            section_name="test",
            journal_name="Test Journal",
            analysis_date="2026-01-16",
            sample_size=1,
            dimensions=dimensions,
        )

        guide = generate_section_guide(style_card)
        print("生成的指南内容:")
        print("=" * 50)
        print(guide)
        print("=" * 50)

        # 保存文件
        output_file = project_root / "simple_test_guide.md"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(guide)
        print(f"指南已保存到: {output_file}")

        return True

    except Exception as e:
        print(f"测试失败: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    test_simple()
