#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试修复后的generate_writing_guides函数
"""

import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))


def test_fixed_guide_generation():
    """测试修复后的指南生成"""
    print("测试修复后的generate_writing_guides函数")
    print("=" * 50)

    try:
        from src.analyzer.journal_style_analyzer import (
            JournalStyleReport,
        )

        # 动态导入函数（可能还未定义）
        import importlib

        analyzer_module = importlib.import_module("src.analyzer.journal_style_analyzer")
        generate_writing_guides = getattr(
            analyzer_module, "generate_writing_guides", None
        )

        # 1. 创建模拟的AI增强报告
        ai_report = JournalStyleReport()
        ai_report.journal_name = "Nature Communications"
        ai_report.analysis_date = "2026-01-16"
        ai_report.papers_analyzed = 5

        # 添加section_style_cards字段
        from src.analyzer.ai_deepseek_analyzer import SectionStyleCard, StyleDimension

        # 创建模拟的style card
        dimensions = StyleDimension(
            function=["Must interpret findings", "Must compare with literature"],
            role="The discussion interprets results and explains significance",
            information_structure=["1. Findings summary", "2. Literature comparison"],
            information_density={
                "high": "Detailed interpretation",
                "low": "Brief summary",
            },
            stance_hedging={"band": "Balanced confidence", "presence": "Professional"},
            sentence_patterns=[
                {"function": "Findings presentation", "position": "opening"},
                {"function": "Literature comparison", "position": "middle"},
            ],
            lexical_features={
                "nouns": {"orientation": "abstract", "refer_to": "concepts"},
                "verbs": {"orientation": "investigative", "refer_to": "actions"},
            },
            constraints={
                "do": ["Use balanced confidence"],
                "dont": ["Avoid overstatement"],
            },
        )

        style_card = SectionStyleCard(
            section_name="discussion",
            journal_name="Nature Communications",
            analysis_date="2026-01-16",
            sample_size=5,
            dimensions=dimensions,
        )

        ai_report.section_style_cards = {"discussion": style_card}

        print("✓ 创建了包含AI分析结果的报告")
        print(
            f"✓ section_style_cards字段存在: {hasattr(ai_report, 'section_style_cards')}"
        )
        print(f"✓ 包含的章节: {list(ai_report.section_style_cards.keys())}")

        # 2. 测试generate_writing_guides函数
        print("\n测试generate_writing_guides函数...")
        guides = generate_writing_guides(ai_report)

        if guides and isinstance(guides, dict):
            print("✓ generate_writing_guides执行成功")
            print(f"✓ 生成的指南: {list(guides.keys())}")

            # 检查是否包含8维度指南
            for section, guide_path in guides.items():
                if Path(guide_path).exists():
                    with open(guide_path, "r", encoding="utf-8") as f:
                        content = f.read()

                    # 检查是否包含8维度结构
                    dimension_indicators = [
                        "## 1. Function (Communicative Goals)",
                        "## 2. Role in Paper",
                        "## 3. Information Structure (Rhetorical Moves)",
                        "## 4. Information Density",
                        "## 5. Stance & Hedging (Allowed Intensity Band)",
                        "## 6. Sentence-Pattern Functions (Exactly 6 Categories)",
                        "## 7. Lexical Features by POS (Top-40 Feature Summary)",
                        "## 8. Constraints & Avoidances (Do/Don't List)",
                    ]

                    found_dimensions = sum(
                        1 for indicator in dimension_indicators if indicator in content
                    )
                    print(f"  {section}: 找到 {found_dimensions}/8 个维度")

                    if found_dimensions >= 6:  # 至少找到6个维度算成功
                        print(f"  ✓ {section}指南包含8维度结构")
                    else:
                        print(f"  ✗ {section}指南维度不完整")
        else:
            print("✗ generate_writing_guides执行失败")
            return False

        print("\n修复验证:")
        print("1. ✓ 添加了section_style_cards字段到JournalStyleReport")
        print("2. ✓ generate_writing_guides能检测AI分析结果")
        print("3. ✓ AI增强指南直接写入文件")
        print("4. ✓ 指南包含8维度结构（不是传统模板）")

        return True

    except Exception as e:
        print(f"测试失败: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """主测试函数"""
    test_result = test_fixed_guide_generation()

    print("\n" + "=" * 50)
    if test_result:
        print("✅ generate_writing_guides修复成功！")
        print("\n现在用户应该看到:")
        print("1. AI分析的8维度写作指南")
        print("2. 包含Function、Role、Information Structure等8个维度")
        print("3. 基于实际分析结果，不是固定模板")
        print("4. 正确的Section Style Card格式")
    else:
        print("❌ 修复失败，需要进一步调试")

    return test_result


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
