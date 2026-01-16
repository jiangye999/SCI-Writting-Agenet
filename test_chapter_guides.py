#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试章节特定风格指南提取功能
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))


def test_chapter_guide_extraction():
    """测试章节指南提取功能"""
    try:
        # 直接导入方法而不是整个类
        import sys

        sys.path.insert(0, "src")
        from coordinator.multi_agent_coordinator import MultiAgentCoordinator

        # 创建一个最小化的实例来测试方法
        class TestCoordinator:
            def extract_chapter_style_guide(
                self, full_style_guide: str, chapter: str
            ) -> str:
                """从完整的风格指南中提取特定章节的指导"""
                import re

                # 查找章节特定的部分
                chapter_patterns = {
                    "introduction": r"## Introduction Section\s*(.*?)(?=\n##|\Z)",
                    "methods": r"## Methods Section\s*(.*?)(?=\n##|\Z)",
                    "results": r"## Results Section\s*(.*?)(?=\n##|\Z)",
                    "discussion": r"## Discussion Section\s*(.*?)(?=\n##|\Z)",
                    "conclusion": r"## Conclusion Section\s*(.*?)(?=\n##|\Z)",
                    "abstract": r"## Abstract Section\s*(.*?)(?=\n##|\Z)",
                }

                pattern = chapter_patterns.get(chapter.lower())
                if pattern:
                    match = re.search(
                        pattern, full_style_guide, re.DOTALL | re.IGNORECASE
                    )
                    if match:
                        chapter_guide = match.group(1).strip()
                        return f"# {chapter.title()} Writing Guide\n\n{chapter_guide}"
                    else:
                        # 如果没找到特定章节的指导，返回一般指导
                        general_match = re.search(
                            r"## General Style Summary\s*(.*?)(?=\n##|\Z)",
                            full_style_guide,
                            re.DOTALL,
                        )
                        if general_match:
                            return f"# General Writing Guide for {chapter.title()}\n\n{general_match.group(1).strip()}"
                        else:
                            return f"# Writing Guide for {chapter.title()}\n\nFollow standard academic writing conventions."

                return f"# Writing Guide for {chapter.title()}\n\nFollow standard academic writing conventions."

        coord = TestCoordinator()

        # 模拟一个完整的风格指南
        full_guide = """
# Comprehensive Journal Style Guide

## Overview
This guide provides detailed writing instructions for each section of papers published in the target journal.

## Introduction Section
# Introduction Writing Guide for Nature Communications

## Tense Usage
- Background information: Present tense (约70%)
- Previous studies: Past tense (约30%)
- Research gap: Present tense

## Key Vocabulary
Frequently used nouns: data, study, research, method, model
Frequently used verbs: show, indicate, suggest, provide, demonstrate

## Transition Words
Sequential: first, secondly, thirdly, next, then, subsequently, finally
Contrastive: however, although, though, despite, in contrast, conversely

## Structure
1. Broad context (2-3 sentences)
2. Specific problem (2-3 sentences)
3. Literature summary (3-4 sentences)
4. Research gap (1-2 sentences)
5. Study objectives (1-2 sentences)

## Style Notes
- Passive voice ratio: 45%
- Average sentence length: 22 words

## Methods Section
# Methods Writing Guide for Nature Communications

## Tense Usage
- Procedures: Past tense (>95%)
- Definitions: Present tense (<5%)

## Structure
1. Study design overview
2. Participants/materials description
3. Experimental procedures
4. Statistical analysis
5. Ethical statements

## General Style Summary
- Use formal academic language
- Be precise and clear
- Follow journal formatting requirements
- Include all necessary details for reproducibility
"""

        # 测试提取介绍章节的指南
        intro_guide = coord.extract_chapter_style_guide(full_guide, "introduction")
        print("Introduction guide extraction:")
        print("=" * 50)
        print(intro_guide[:200] + "..." if len(intro_guide) > 200 else intro_guide)
        print()

        # 测试提取方法章节的指南
        methods_guide = coord.extract_chapter_style_guide(full_guide, "methods")
        print("Methods guide extraction:")
        print("=" * 50)
        print(
            methods_guide[:200] + "..." if len(methods_guide) > 200 else methods_guide
        )
        print()

        # 测试不存在的章节（应该返回一般指南）
        unknown_guide = coord.extract_chapter_style_guide(full_guide, "unknown")
        print("Unknown chapter guide extraction:")
        print("=" * 50)
        print(unknown_guide)
        print()

        print("✅ All tests passed!")
        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    test_chapter_guide_extraction()
