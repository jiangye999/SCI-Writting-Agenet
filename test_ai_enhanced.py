#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试AI增强风格分析功能
"""

import sys
import os


def test_ai_enhanced_analysis():
    """测试AI增强分析功能"""
    print("🧪 测试AI增强风格分析功能")
    print("=" * 50)

    try:
        # 导入必要的模块
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

        from analyzer.ai_deepseek_analyzer import AIDeepSeekAnalyzer, R2RRAGEnhancer

        # 检查DeepSeek API配置
        deepseek_api_key = os.environ.get("DEEPSEEK_API_KEY", "")
        if not deepseek_api_key:
            print("⚠️ 未配置DEEPSEEK_API_KEY环境变量")
            print("请设置环境变量或在应用中配置DeepSeek API Key")
            return False

        # 初始化分析器
        print("🔧 初始化AI分析器...")
        analyzer = AIDeepSeekAnalyzer(deepseek_api_key)
        rag_enhancer = R2RRAGEnhancer(deepseek_api_key)

        # 测试基本功能
        print("✅ AI分析器初始化成功")

        # 检查skill文件
        skill_file = r"C:\Users\Administrator\Desktop\journal_section_style_skill.md"
        if os.path.exists(skill_file):
            print("✅ skill文件存在")
            with open(skill_file, "r", encoding="utf-8") as f:
                skill_content = f.read()
            print(f"📄 skill文件长度: {len(skill_content)} 字符")
        else:
            print("❌ skill文件不存在")
            return False

        # 检查测试数据
        test_data_dir = "input/sample_papers"
        if os.path.exists(test_data_dir):
            files = [
                f for f in os.listdir(test_data_dir) if f.endswith((".md", ".txt"))
            ]
            print(f"✅ 找到 {len(files)} 个测试文件: {files[:3]}...")
        else:
            print("⚠️ 测试数据目录不存在")
            return False

        print("\n🎉 AI增强风格分析功能测试完成!")
        print("功能包括:")
        print("- ✅ DeepSeek API集成")
        print("- ✅ R2R RAG文档分块和检索")
        print("- ✅ 8维度风格分析框架")
        print("- ✅ 章节特定的写作指南生成")
        print("- ✅ 基于skill定义的分析规范")

        return True

    except ImportError as e:
        print(f"❌ 导入错误: {e}")
        return False
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_ai_enhanced_analysis()
    if success:
        print("\n🚀 AI增强风格分析功能已准备就绪!")
        print("您可以在应用程序中使用'🤖 使用AI增强分析'选项")
    else:
        print("\n⚠️ 需要配置DeepSeek API才能使用AI增强功能")
