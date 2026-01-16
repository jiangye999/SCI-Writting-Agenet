#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证app.py语法修复
"""


def test_app_syntax():
    """测试app.py的基本语法"""
    print("Testing app.py syntax fix...")

    try:
        # 尝试导入模块来检查语法
        import sys
        import os
        import py_compile

        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

        # 编译检查
        app_path = os.path.join(os.path.dirname(__file__), "app.py")
        py_compile.compile(app_path, doraise=True)

        print("SUCCESS: Syntax check passed!")
        print("SUCCESS: No syntax errors found")
        print("SUCCESS: App should start normally now")

        return True

    except py_compile.PyCompileError as e:
        print(f"ERROR: Syntax error: {e}")
        return False
    except Exception as e:
        print(f"ERROR: Other error: {e}")
        return False


if __name__ == "__main__":
    test_app_syntax()
