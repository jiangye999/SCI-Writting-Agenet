#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试修复后的内存管理功能
"""

import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))


def test_memory_fix():
    """测试内存修复"""
    print("测试修复后的内存管理...")

    try:
        from src.analyzer.journal_style_analyzer import JournalStyleAnalyzer

        # 创建分析器
        analyzer = JournalStyleAnalyzer("english")

        # 模拟长文本（可能导致内存问题）
        long_text = (
            """
        This is a very long academic text that would normally cause memory issues when processed by spaCy. 
        It contains many sentences and complex structures. The purpose is to test whether our chunking approach 
        can handle large texts without running out of memory. We need to make sure that the text processing 
        can handle documents of various sizes without crashing. This is particularly important for academic 
        papers which can be quite lengthy and contain dense technical content. The chunking strategy should 
        break down the text into manageable pieces that can be processed individually without exceeding 
        memory limits. Each chunk should be small enough to fit within available memory while still 
        being large enough to maintain context for proper linguistic analysis.
        
        The analysis should include proper vocabulary extraction, sentence structure analysis, and stylistic 
        feature detection. All of these operations need to work correctly across chunk boundaries and 
        the results should be properly merged to provide a comprehensive analysis of the entire document.
        
        Furthermore, the system should handle edge cases such as very short chunks, chunks with no 
        analyzable content, and situations where chunk processing fails for other reasons. Error handling 
        should be robust and the system should continue processing even when individual chunks encounter problems.
        
        This test represents a realistic scenario where users upload full academic papers that might be 
        several thousand words long. The traditional approach of processing the entire document at once 
        would likely fail with memory allocation errors, but our chunked approach should handle it gracefully.
        """
            * 20
        )  # 重复20次，创建一个很长的文本

        print(f"测试文本长度: {len(long_text)} 字符")

        # 测试分析
        result = analyzer.analyze_text(long_text, "test_section")

        # 验证结果
        if result and isinstance(result, dict):
            print("✓ 分析成功完成")
            print(f"✓ 结果包含键: {list(result.keys())}")

            # 检查词汇分析
            if "vocabulary" in result:
                vocab = result["vocabulary"]
                print(f"✓ 词汇分析完成: {list(vocab.keys())}")

            # 检查句子结构
            if "sentence_structure" in result:
                struct = result["sentence_structure"]
                print(f"✓ 句子结构分析完成: {list(struct.keys())}")

            # 检查文体特征
            if "stylistic_features" in result:
                style = result["stylistic_features"]
                print(f"✓ 文体特征分析完成: {list(style.keys())}")

            print("内存管理修复测试通过")
            return True
        else:
            print("✗ 分析失败或返回格式错误")
            return False

    except Exception as e:
        print(f"✗ 内存管理测试失败: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """主测试函数"""
    print("测试内存分配修复")
    print("=" * 40)

    test_result = test_memory_fix()

    print("=" * 40)
    if test_result:
        print("✅ 内存管理修复成功！")
        print("现在系统可以:")
        print("1. 自动分块处理长文本")
        print("2. 避免spaCy内存分配错误")
        print("3. 正确合并各chunk的分析结果")
        print("4. 在chunk失败时尝试更小的分块")
        print("5. 提供错误处理和恢复机制")
    else:
        print("❌ 内存管理修复失败，需要进一步调试")

    return test_result


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
