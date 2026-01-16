#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证增强的期刊风格分析功能
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))


def test_enhanced_analysis():
    """测试增强的分析功能"""
    try:
        from analyzer.journal_style_analyzer import JournalStyleAnalyzer

        # 创建分析器
        analyzer = JournalStyleAnalyzer()

        # 模拟文本分析
        sample_text = """
        The deep learning model was developed using convolutional neural networks.
        Previous studies have shown that CNNs are effective for image classification tasks.
        However, the performance depends on several factors including dataset size and architecture.
        In this study, we investigated the impact of different activation functions on model accuracy.
        The results indicate that ReLU activation provides better performance compared to sigmoid.
        Furthermore, the model achieved 95% accuracy on the test dataset.
        """

        # 测试analyze_text方法
        result = analyzer.analyze_text(sample_text, "introduction")

        # 验证新功能
        checks = {
            "nouns": "nouns" in result,
            "verbs": "verbs" in result,
            "adjectives": "adjectives" in result,
            "adverbs": "adverbs" in result,
            "prepositions": "prepositions" in result,
            "conjunction_counts": "conjunction_counts" in result,
            "sentence_length_distribution": "sentence_length_distribution" in result,
            "sentence_types": "sentence_types" in result,
        }

        print("Enhanced Analysis Features Check:")
        for feature, present in checks.items():
            status = "✓" if present else "✗"
            print(f"  {status} {feature}")

        # 检查数据内容
        if checks["nouns"]:
            print(f"  Nouns found: {len(result['nouns'])}")
        if checks["adjectives"]:
            print(f"  Adjectives found: {len(result['adjectives'])}")
        if checks["sentence_types"]:
            print(f"  Sentence types: {result['sentence_types']}")

        all_passed = all(checks.values())
        print(
            f"\n{'✅ All enhanced features working!' if all_passed else '❌ Some features missing'}"
        )

        return all_passed

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    test_enhanced_analysis()
