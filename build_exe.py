# -*- coding: utf-8 -*-
"""
论文写作助手 - 打包配置
Paper Writing Assistant - Build Configuration for PyInstaller
"""

import os
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.resolve()

# 应用程序信息
APP_NAME = "PaperWriter"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = "基于AI的多代理学术论文写作系统"

# 需要包含的数据文件
DATA_FILES = [
    # 配置文件
    ("config/config.yaml", "config/"),
    # 模板文件
    ("src/coordinator/prompts/", "src/coordinator/prompts/"),
]

# 需要包含的Python包
imports = [
    # 核心依赖
    "streamlit",
    "pandas",
    "openpyxl",
    "PyYAML",
    "spacy",
    "nltk",
    "requests",
    # 本项目模块
    "src.config",
    "src.analyzer",
    "src.analyzer.journal_style_analyzer",
    "src.literature",
    "src.literature.db_manager",
    "src.coordinator",
    "src.coordinator.multi_agent_coordinator",
    "src.integrator",
    "src.integrator.draft_integrator",
    "src.model_router",
    "src.document_processor",
    "src.document_processor.simple_parser",
]

# 排除的文件和目录
excludes = [
    # 测试相关
    "pytest",
    "pytest-*",
    "tests",
    "test_*",
    # 文档
    "docs",
    "*.md",
    "*.rst",
    # 开发工具
    "pyinstaller",
    "setuptools",
    "wheel",
    # 虚拟环境
    "venv",
    ".venv",
    "env",
    # 其他
    "tkinter",  # 如果不需要GUI
    "PyQt5",  # 如果不需要Qt
]

# 隐藏导入（可选，用于减少打包体积）
hidden_imports = [
    "streamlit.runtime.scriptrunner",
    "streamlit.runtime.caching",
    "pandas.io.excel",
    "openpyxl.load_workbook",
    "spacy",
    "spacy.lang.en",
    "nltk",
    "nltk.tokenize",
    "nltk.corpus",
    "yaml",
    "requests",
    "urllib3",
]

# 分析器选项
a = Analysis(
    [],
    pathex=[str(PROJECT_ROOT)],
    binaries=[],
    datas=DATA_FILES,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

# 打包选项
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

# exe配置
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name=APP_NAME,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # 如果需要控制台输出，设为True；否则设为False
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # 可以添加图标: icon="icon.ico"
)

# 如果需要窗口模式（无控制台）
# exe = EXE(
#     pyz,
#     a.scripts,
#     [],
#     exclude=[],
#     name=APP_NAME,
#     debug=False,
#     bootloader_ignore_signals=False,
#     strip=False,
#     upx=True,
#     console=False,
#     disable_windowed_traceback=False,
#     icon=None,
# )
