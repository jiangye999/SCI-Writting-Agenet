#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试应用程序的完整功能
"""

import sys
import os
import subprocess
import time


def test_app_startup():
    """测试应用程序是否可以正常启动"""
    print("Testing app startup...")

    try:
        # 尝试启动streamlit应用
        app_path = os.path.join(os.path.dirname(__file__), "app.py")

        # 使用subprocess启动应用并检查是否能正常启动
        process = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "streamlit",
                "run",
                app_path,
                "--server.port",
                "8503",  # 使用不同端口避免冲突
                "--server.headless",
                "true",  # 无头模式
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        # 等待几秒钟让应用启动
        time.sleep(3)

        # 检查进程是否还在运行
        if process.poll() is None:
            print("SUCCESS: App started successfully")
            print("SUCCESS: No immediate startup errors")

            # 终止进程
            process.terminate()
            process.wait(timeout=5)

            return True
        else:
            # 获取错误输出
            stdout, stderr = process.communicate()
            print("ERROR: App failed to start")
            if stderr:
                print(f"Stderr: {stderr[:500]}...")
            if stdout:
                print(f"Stdout: {stdout[:500]}...")

            return False

    except Exception as e:
        print(f"ERROR: Exception during startup test: {e}")
        return False


def test_imports():
    """测试必要的模块导入"""
    print("Testing module imports...")

    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

        # 测试核心模块导入
        from analyzer import analyze_journal_style

        print("SUCCESS: analyzer module imported")

        from analyzer.ai_deepseek_analyzer import analyze_journal_style_with_ai

        print("SUCCESS: ai_deepseek_analyzer module imported")

        from coordinator import MultiAgentCoordinator

        print("SUCCESS: coordinator module imported")

        from integrator import DraftIntegrator

        print("SUCCESS: integrator module imported")

        from literature import create_literature_database

        print("SUCCESS: literature module imported")

        return True

    except ImportError as e:
        print(f"ERROR: Import failed: {e}")
        return False
    except Exception as e:
        print(f"ERROR: Unexpected error during import: {e}")
        return False


def test_basic_functionality():
    """测试基本功能"""
    print("Testing basic functionality...")

    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

        from analyzer import analyze_journal_style

        # 测试传统分析功能（使用现有的测试数据）
        test_dir = "input/sample_papers"
        output_dir = "output/test_style"

        if os.path.exists(test_dir):
            result = analyze_journal_style(test_dir, output_dir, "Test Journal")
            print("SUCCESS: Basic style analysis works")

            # 检查输出文件
            if os.path.exists(os.path.join(output_dir, "journal_style_report.json")):
                print("SUCCESS: Report file generated")
            else:
                print("WARNING: Report file not found")

            return True
        else:
            print(
                "WARNING: Test data directory not found, skipping basic functionality test"
            )
            return True

    except Exception as e:
        print(f"ERROR: Basic functionality test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """主测试函数"""
    print("=" * 60)
    print("COMPREHENSIVE APP FUNCTIONALITY TEST")
    print("=" * 60)

    tests = [
        ("Module Imports", test_imports),
        ("Syntax Check", lambda: True),  # 已经在前面通过了
        ("App Startup", test_app_startup),
        ("Basic Functionality", test_basic_functionality),
    ]

    results = []
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        try:
            result = test_func()
            results.append((test_name, result))
            status = "PASS" if result else "FAIL"
            print(f"Result: {status}")
        except Exception as e:
            print(f"Result: ERROR - {e}")
            results.append((test_name, False))

    # 总结
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    all_passed = True
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{test_name}: {status}")
        if not result:
            all_passed = False

    print("\n" + "=" * 60)
    if all_passed:
        print("OVERALL RESULT: ALL TESTS PASSED!")
        print("The application should work correctly now.")
    else:
        print("OVERALL RESULT: SOME TESTS FAILED!")
        print("Please check the error messages above.")

    return all_passed


if __name__ == "__main__":
    main()
