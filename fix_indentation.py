#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复ai_deepseek_analyzer.py的缩进问题
"""


def fix_indentation():
    """修复第686行的缩进问题"""
    file_path = (
        r"E:\AI_projects\学术写作\paper_writer\src\analyzer\ai_deepseek_analyzer.py"
    )

    # 读取文件
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # 找到第686行（索引685，因为从0开始）
    if len(lines) > 686:
        line_686 = lines[686]
        print(f"第686行原始内容: {repr(line_686)}")

        # 修复缩进 - 替换为正确的4个空格
        if "        if style_cards" in line_686:
            fixed_line = "        if style_cards"  # 4个空格
            lines[686] = fixed_line
            print(f"修复后: {repr(fixed_line)}")

            # 写回文件
            with open(file_path, "w", encoding="utf-8") as f:
                f.writelines(lines)

            print("✓ 缩进问题已修复")
            return True

    print("✗ 找不到第686行")
    return False


if __name__ == "__main__":
    success = fix_indentation()
    if success:
        print("缩进修复完成，现在可以正常运行app.py")
    else:
        print("缩进修复失败")
