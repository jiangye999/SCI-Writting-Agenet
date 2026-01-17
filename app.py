# -*- coding: utf-8 -*-
"""
论文写作助手 - Web界面（自动整合版）
Paper Writing Assistant - Web UI (Auto-Integration)
"""

import streamlit as st
import os
import sys
import tempfile
import requests
import json
import pandas as pd
import sqlite3
import io
from pathlib import Path
import shutil
import time
import traceback

# 添加src到路径
project_root = str(Path(__file__).parent.resolve())
src_path = os.path.join(project_root, "src")
sys.path.insert(0, src_path)

# 页面配置
st.set_page_config(
    page_title="论文写作助手",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 导入模块
from analyzer import analyze_journal_style
from analyzer.ai_deepseek_analyzer import analyze_journal_style_with_ai
from literature import create_literature_database, LiteratureDatabaseManager
# from coordinator import MultiAgentCoordinator  # 暂时注释掉
# from integrator import DraftIntegrator  # 暂时注释掉

# 标题
st.title("📝 论文写作助手")
st.markdown("基于AI的多代理学术论文写作系统")

# Sidebar
with st.sidebar:
    st.header("⚙️ 配置")

    # Clean the URL - remove /v1 suffix if user entered it
    default_url = ""
    api_url = st.text_input(
        "API代理地址",
        value=default_url,
        help="完整的API代理地址，包含/v1路径",
        key="api_url_input",
    )

    # 只去除末尾的斜杠，保留/v1
    if api_url.endswith("/"):
        api_url = api_url[:-1]

    api_key = st.text_input(
        "API Key",
        type="password",
        value="",
        help="输入你的API Key用于访问AI模型",
        key="api_key_input",
    )

    if api_key and api_url:
        st.success("API已配置")
    elif api_url and not api_key:
        st.warning("请输入API Key")
    elif api_key and not api_url:
        st.warning("请输入API代理地址")
    else:
        st.info("请配置API连接")

    # Verify API connection
    if st.button("验证API连接", type="primary"):
        if not api_url or not api_key:
            st.error("请同时输入API地址和API Key")
        else:
            try:
                # Test connection - remove trailing slash if present
                base_url = api_url.rstrip("/")
                test_url = f"{base_url}/models"

                headers = {"Authorization": f"Bearer {api_key}"}
                response = requests.get(test_url, headers=headers, timeout=5)

                if response.status_code == 200:
                    try:
                        data = response.json()
                        models = data.get("data", [])
                        st.success("API连接成功！")
                        st.write(f"可用模型: {len(models)} 个")
                        if models:
                            with st.expander("查看模型列表"):
                                for m in models[:10]:
                                    st.write(f"- {m.get('id', 'Unknown')}")
                                if len(models) > 10:
                                    st.write(f"... 共 {len(models)} 个模型")
                    except Exception:
                        # 返回200但不是JSON，可能是代理返回了其他内容
                        st.warning(
                            "API连接正常，但返回格式异常。代理可能不支持/models端点。"
                        )
                elif response.status_code == 401:
                    st.error("连接失败: API Key无效")
                elif response.status_code == 404:
                    st.error("连接失败: 端点不存在，请检查API地址是否正确")
                else:
                    st.error(f"连接失败: HTTP {response.status_code}")
            except requests.exceptions.ConnectionError:
                st.error("连接失败: 无法连接到API服务器，请检查URL是否正确")
            except Exception as e:
                st.error(f"连接失败: {str(e)[:100]}")

    # DeepSeek配置 - 用于增强特征提取
    st.header("🤖 DeepSeek 配置")
    st.markdown("用于高级风格特征提取和RAG增强分析")

    deepseek_api_key = st.text_input(
        "DeepSeek API Key",
        type="password",
        value="",
        help="输入DeepSeek API Key用于增强特征提取功能",
        key="deepseek_api_key_input",
    )

    deepseek_base_url = st.text_input(
        "DeepSeek Base URL",
        value="https://api.deepseek.com/v1",
        help="DeepSeek API的基础URL",
        key="deepseek_base_url_input",
    )

    if deepseek_api_key:
        st.success("✅ DeepSeek API已配置")
    else:
        st.info("💡 配置DeepSeek API以启用增强特征提取")

    st.info("""
    📌 使用说明

    1. 确保API代理正在运行
    2. 填入正确的API Key
    3. 配置DeepSeek API用于增强特征提取
    4. 上传研究背景文件
    5. 点击"开始写作"即可
    """)

# 主界面 - 选项卡
tab1, tab2, tab3, tab4 = st.tabs(
    ["📊 风格分析", "📚 文献导入", "✍️ 一键写作", "💡 了解更多"]
)

# ========== Tab 1: 风格分析 ==========
with tab1:
    st.header("期刊风格分析")
    st.markdown("分析范文样本，提取目标期刊的写作风格")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📤 上传论文范文")
        uploaded_papers = st.file_uploader(
            "选择论文文件（支持PDF/Word/Markdown/TXT）",
            type=["pdf", "docx", "doc", "md", "txt"],
            accept_multiple_files=True,
            key="papers_uploader",
        )
        st.info(
            "💡 **提示**：上传的论文范文与你的研究主题越相关，分析结果越准确，生成的论文风格越贴近目标期刊"
        )

        # 初始化session state
        if "temp_papers_dir" not in st.session_state:
            st.session_state.temp_papers_dir = None
        if "uploaded_papers" not in st.session_state:
            st.session_state.uploaded_papers = None

        # 初始化风格分析选项（用于固定选项功能）
        if "style_analysis_options" not in st.session_state:
            st.session_state.style_analysis_options = {
                "selected_sections": [
                    "abstract",
                    "introduction",
                    "methods",
                    "results",
                    "discussion",
                    "conclusion",
                ],
                "fixed_options": [
                    "abstract",
                    "introduction",
                    "methods",
                    "results",
                    "discussion",
                    "conclusion",
                ],
            }

        # 定义所有可用的章节选项
        ALL_SECTION_OPTIONS = [
            {"value": "abstract", "label": "📄 摘要 (Abstract)"},
            {"value": "introduction", "label": "📝 引言 (Introduction)"},
            {"value": "methods", "label": "🔬 方法 (Methods)"},
            {"value": "results", "label": "📊 结果 (Results)"},
            {"value": "discussion", "label": "💬 讨论 (Discussion)"},
            {"value": "conclusion", "label": "✨ 结论 (Conclusion)"},
        ]

        # 如果用户上传了新文件，更新session state并保存到临时目录
        if uploaded_papers:
            st.session_state.uploaded_papers = uploaded_papers
            # 重新创建临时目录（确保每次都写入文件）
            if st.session_state.temp_papers_dir and os.path.exists(
                st.session_state.temp_papers_dir
            ):
                shutil.rmtree(st.session_state.temp_papers_dir)
            st.session_state.temp_papers_dir = tempfile.mkdtemp()
            file_count = 0
            for f in st.session_state.uploaded_papers:
                try:
                    file_path = os.path.join(st.session_state.temp_papers_dir, f.name)
                    with open(file_path, "wb") as file:
                        file.write(f.getbuffer())
                    file_count += 1
                    st.write(f"✅ 已保存: {f.name}")
                except Exception as e:
                    st.error(f"❌ 保存失败 {f.name}: {str(e)}")
            st.success(f"已上传 {file_count} 个文件")
        else:
            # 调试信息：显示当前状态
            if st.session_state.uploaded_papers:
                st.info(
                    f"已选择 {len(st.session_state.uploaded_papers)} 个文件（来自session）"
                )

    with col2:
        st.subheader("📂 或使用本地文件")
        use_local = st.checkbox("使用本地范文", value=True, key="use_local_papers_2")
        local_dir = "input/sample_papers"
        if use_local:
            local_dir = st.text_input(
                "范文目录", value="input/sample_papers", key="local_dir_input"
            )

        journal_name = st.text_input(
            "目标期刊", value="Nature Communications", key="journal_name_input"
        )

        # AI增强分析选项
        use_ai_enhancement = st.checkbox(
            "🤖 使用AI增强分析",
            value=True,  # 改为默认开启
            help="使用DeepSeek AI进行8维度深度风格分析（需要配置DeepSeek API）",
            key="use_ai_enhancement",
        )

        if use_ai_enhancement:
            if not deepseek_api_key:
                st.warning("⚠️ 使用AI增强分析需要配置DeepSeek API Key")
            else:
                st.info(
                    "✅ 将使用AI增强分析，基于journal_section_style_skill.md的8维度框架"
                )

    # 根据用户选择确定使用的目录
    if st.session_state.uploaded_papers:
        papers_dir = st.session_state.temp_papers_dir
    elif use_local:
        papers_dir = local_dir
    else:
        papers_dir = None

    if st.button("🔍 分析风格", type="primary"):
        if (
            not papers_dir
            or not os.path.exists(papers_dir)
            or not os.listdir(papers_dir)
        ):
            st.warning("请上传文件或确保本地目录有文件")
        else:
            # 分析进度条和状态
            progress_bar = st.progress(0)
            status_text = st.empty()

            with st.spinner("🔍 正在分析期刊风格..."):
                try:
                    status_text.text("正在初始化分析器...")
                    progress_bar.progress(10)

                    status_text.text("正在处理论文文本...")
                    progress_bar.progress(30)

                    status_text.text("正在分析词汇特征...")
                    progress_bar.progress(50)

                    status_text.text("正在生成写作指南...")
                    progress_bar.progress(80)

                    # 执行实际分析
                    if use_ai_enhancement and deepseek_api_key:
                        # 使用AI增强分析
                        skill_file_path = r"E:\AI_projects\学术写作\paper_writer\journal_section_style_skill.md"
                        if os.path.exists(skill_file_path):
                            result = analyze_journal_style_with_ai(
                                papers_dir,
                                "output/style",
                                journal_name,
                                deepseek_api_key,
                            )
                            st.info("✅ 使用AI增强分析完成（严格按照skill 8维度框架）")
                        else:
                            st.warning("⚠️ skill文件不存在，将使用传统分析")
                            result = analyze_journal_style(
                                papers_dir, "output/style", journal_name
                            )
                    else:
                        # 使用传统分析
                        result = analyze_journal_style(
                            papers_dir, "output/style", journal_name
                        )

                    status_text.text("完成！")
                    progress_bar.progress(100)

                    st.success("✅ 分析完成!")

                    # 显示结果摘要
                    st.subheader("📊 分析结果")

                    # 读取并显示风格摘要
                    if os.path.exists(result["summary"]):
                        with open(result["summary"], "r", encoding="utf-8") as f:
                            summary_content = f.read()
                        st.markdown(summary_content)

                    # 显示生成的文件
                    st.subheader("📁 生成的文件")

                    col1, col2 = st.columns(2)

                    with col1:
                        st.write("**核心文件**")
                        if os.path.exists(result["report"]):
                            st.write(
                                f"📄 完整报告: {os.path.basename(result['report'])}"
                            )
                        if os.path.exists(result["summary"]):
                            st.write(
                                f"📄 风格摘要: {os.path.basename(result['summary'])}"
                            )

                    with col2:
                        st.write("**写作指南**")
                        if "guides" in result and isinstance(result["guides"], dict):
                            for section, guide_path in result["guides"].items():
                                if os.path.exists(guide_path):
                                    st.write(
                                        f"📄 {section.title()}指南: {os.path.basename(guide_path)}"
                                    )

                    # 添加下载按钮
                    st.subheader("📥 下载结果")

                    # 检查输出目录是否存在
                    style_dir = "output/style"
                    if os.path.exists(style_dir) and os.listdir(style_dir):
                        import zipfile
                        import io

                        try:
                            zip_buffer = io.BytesIO()
                            with zipfile.ZipFile(
                                zip_buffer, "w", zipfile.ZIP_DEFLATED
                            ) as zipf:
                                for root, dirs, files in os.walk(style_dir):
                                    for file in files:
                                        file_path = os.path.join(root, file)
                                        arcname = os.path.relpath(file_path, style_dir)
                                        zipf.write(file_path, arcname)

                            zip_buffer.seek(0)
                            zip_data = zip_buffer.getvalue()

                            # 使用 Streamlit 的下载按钮
                            st.download_button(
                                label="📦 下载所有分析结果 (ZIP)",
                                data=zip_data,
                                file_name="style_analysis.zip",
                                mime="application/zip",
                                help="下载包含所有分析结果的压缩包",
                            )
                            st.success("✅ 压缩包已准备就绪，点击上方按钮下载")

                        except Exception as e:
                            st.error(f"创建压缩包失败: {str(e)}")
                    else:
                        st.warning("没有找到分析结果文件，无法创建下载包")

                    # 显示详细的文件路径
                    with st.expander("📂 完整文件路径"):
                        for key, value in result.items():
                            if isinstance(value, dict):
                                for sub_key, sub_path in value.items():
                                    if os.path.exists(sub_path):
                                        st.write(f"📄 {key}/{sub_key}: {sub_path}")
                            else:
                                if os.path.exists(value):
                                    st.write(f"📄 {key}: {value}")

                except Exception as e:
                    st.error(f"分析失败: {str(e)}")
                    st.error(f"错误详情: {traceback.format_exc()}")

    # 清理临时文件 - 只在用户点击时清理
    if st.session_state.temp_papers_dir and os.path.exists(
        st.session_state.temp_papers_dir
    ):
        if st.button("🗑️ 清理临时文件"):
            try:
                shutil.rmtree(st.session_state.temp_papers_dir)
                st.session_state.temp_papers_dir = None
                st.session_state.uploaded_papers = None
                st.success("临时文件已清理")
            except Exception as e:
                st.error(f"清理失败: {str(e)}")

# ========== Tab 2: 文献导入 ==========
with tab2:
    st.header("📚 文献数据库管理")
    st.markdown("导入Web of Science导出的Plain Text文献数据")

    # ========== 上传文献文件 ==========
    st.subheader("📤 上传WOS文献文件")
    st.markdown("上传Web of Science导出的 **Plain Text / Full Record** 格式")
    st.caption("支持批量上传多个.txt文件")

    uploaded_literature_list = st.file_uploader(
        "选择文献文件",
        type=["txt"],
        accept_multiple_files=True,
    )

    st.info(
        "💡 **提示**：导出时选择 **Full Record** 格式，确保包含摘要(AB)和作者(AU)字段。"
    )

    # 处理上传的文件
    txt_files_info = []  # 存储 (文件名, 临时路径)
    temp_lit_dir = None

    if uploaded_literature_list:
        temp_lit_dir = tempfile.mkdtemp()
        file_count = 0
        for uploaded_file in uploaded_literature_list:
            path = os.path.join(temp_lit_dir, uploaded_file.name)
            with open(path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            txt_files_info.append((uploaded_file.name, path))
            file_count += 1
        st.success(f"已上传 {file_count} 个文件")

    # 导入按钮（批量导入）
    if txt_files_info:
        if st.button("📥 导入所有文献文件", type="primary"):
            with st.spinner("导入中..."):
                imported_count = 0
                error_count = 0
                for file_name, file_path in txt_files_info:
                    # 为每个文件创建独立的数据库
                    safe_name = (
                        file_name.replace(" ", "_")
                        .replace("-", "_")
                        .replace(".txt", "")
                    )
                    db_path = f"output/{safe_name}.db"

                    try:
                        # 检查源文件是否存在且有内容
                        if not os.path.exists(file_path):
                            st.error(f"❌ 文件不存在: {file_name}")
                            error_count += 1
                            continue

                        file_size = os.path.getsize(file_path)
                        if file_size == 0:
                            st.error(f"❌ 文件为空: {file_name}")
                            error_count += 1
                            continue

                        # 导入到数据库
                        manager = create_literature_database(file_path, db_path)
                        stats = manager.get_statistics()

                        if stats["total_papers"] > 0:
                            imported_count += 1
                            st.success(
                                f"✅ {file_name}: {stats['total_papers']} 篇文献"
                            )
                        else:
                            st.warning(
                                f"⚠️ {file_name}: 0 篇文献（文件可能为空或格式不对）"
                            )
                            error_count += 1

                    except Exception as e:
                        st.error(f"❌ 导入失败: {file_name} - {str(e)}")
                        error_count += 1

                # 显示总结
                if imported_count > 0:
                    st.success(
                        f"✅ 成功导入 {imported_count}/{len(txt_files_info)} 个文件"
                    )
                    st.rerun()
                else:
                    st.error(
                        f"❌ 导入失败，所有 {len(txt_files_info)} 个文件都导入失败"
                    )

    # 清理临时文件
    if uploaded_literature_list and temp_lit_dir and os.path.exists(temp_lit_dir):
        try:
            shutil.rmtree(temp_lit_dir)
        except:
            pass

    st.divider()

    # ========== 选择要查看的文献文件 ==========
    st.subheader("📂 选择要查看的文献文件")

    # 获取所有已导入的数据库文件
    output_dir = "output"
    if os.path.exists(output_dir):
        db_files = [
            f.replace(".db", "") for f in os.listdir(output_dir) if f.endswith(".db")
        ]
    else:
        db_files = []

    if not db_files:
        st.info("暂无已导入的文献库，请先上传并导入文献文件")
    else:
        # 下拉菜单选择 + 删除按钮
        col1, col2 = st.columns([3, 1])
        with col1:
            selected_db_name = st.selectbox(
                "选择文献文件",
                options=db_files,
                key="file_selector",
            )
        with col2:
            st.write("")  # 占位对齐
            st.write("")  # 占位对齐
            if st.button("🗑️ 删除", type="secondary", use_container_width=True):
                db_path = f"output/{selected_db_name}.db"
                if os.path.exists(db_path):
                    os.remove(db_path)
                    st.success("已删除")
                    st.rerun()

        # 数据库路径
        db_path = f"output/{selected_db_name}.db"

        if os.path.exists(db_path):
            st.success(f"已加载: {selected_db_name}")

        st.divider()

        # ========== 三个下载卡片 ==========
        st.subheader("📦 导出文件")

        has_data = False
        jsonl_content = ""
        bibtex_content = ""
        excel_buffer = io.BytesIO()
        jsonl_count = 0
        bib_count = 0
        excel_count = 0

        if os.path.exists(db_path):
            try:
                manager = LiteratureDatabaseManager(db_path)
                stats = manager.get_statistics()

                if stats["total_papers"] > 0:
                    has_data = True
                    papers = manager.search("", limit=10000)

                    # JSONL数据
                    jsonl_lines = []
                    for paper in papers:
                        first_author = ""
                        if paper.authors:
                            first_author = (
                                paper.authors.split(",")[0].strip().split()[-1]
                            )
                        citation_text = (
                            f"({first_author} et al., {paper.year})"
                            if first_author and paper.year
                            else ""
                        )

                        jsonl_lines.append(
                            json.dumps(
                                {
                                    "paper_id": paper.wos_id or f"id_{paper.id}",
                                    "title": paper.title,
                                    "year": paper.year,
                                    "authors": paper.authors.split("; ")
                                    if paper.authors
                                    else [],
                                    "first_author_lastname": first_author,
                                    "doi": paper.doi,
                                    "abstract": paper.abstract,
                                    "citation_text": citation_text,
                                    "source": "Web of Science",
                                },
                                ensure_ascii=False,
                            )
                        )
                    jsonl_content = "\n".join(jsonl_lines)
                    jsonl_count = len(jsonl_lines)

                    # BibTeX数据
                    bibtex_content = manager.export_to_bibtex()
                    bib_count = bibtex_content.count("@article")

                    # Excel数据
                    papers_data = []
                    for paper in papers:
                        papers_data.append(
                            {
                                "Authors": paper.authors,
                                "Title": paper.title,
                                "Journal": paper.journal,
                                "Year": paper.year,
                                "Volume": paper.volume,
                                "DOI": paper.doi,
                                "Abstract": paper.abstract,
                                "Cited By": paper.cited_by,
                            }
                        )
                    excel_buffer = io.BytesIO()
                    pd.DataFrame(papers_data).to_excel(
                        excel_buffer, index=False, engine="openpyxl"
                    )
                    excel_buffer.seek(0)
                    excel_count = len(papers_data)
            except Exception as e:
                st.warning(f"加载数据失败: {str(e)}")

        # 显示三个卡片
        col_card1, col_card2, col_card3 = st.columns(3)

        # 卡片1: JSONL
        with col_card1:
            with st.container(border=True):
                st.markdown(
                    """
                <div style="text-align: center; padding: 10px;">
                    <span style="font-size: 40px;">📄</span>
                    <h4 style="margin: 10px 0;">JSONL</h4>
                    <p style="color: gray; font-size: 12px;">结构化文献数据</p>
                </div>
                """,
                    unsafe_allow_html=True,
                )
                if has_data:
                    st.write(f"📊 共 **{jsonl_count}** 条记录")
                    st.download_button(
                        label="📥 下载JSONL",
                        data=jsonl_content,
                        file_name=f"{selected_db_name}.jsonl",
                        mime="application/json",
                        use_container_width=True,
                    )
                else:
                    st.write("📊 共 **0** 条记录")
                    st.download_button(
                        label="📥 下载JSONL",
                        data="",
                        file_name="literature.jsonl",
                        mime="application/json",
                        use_container_width=True,
                        disabled=True,
                    )

        # 卡片2: BibTeX
        with col_card2:
            with st.container(border=True):
                st.markdown(
                    """
                <div style="text-align: center; padding: 10px;">
                    <span style="font-size: 40px;">📚</span>
                    <h4 style="margin: 10px 0;">BibTeX</h4>
                    <p style="color: gray; font-size: 12px;">参考文献格式</p>
                </div>
                """,
                    unsafe_allow_html=True,
                )
                if has_data:
                    st.write(f"📊 共 **{bib_count}** 条引用")
                    st.download_button(
                        label="📥 下载BibTeX",
                        data=bibtex_content,
                        file_name=f"{selected_db_name}.bib",
                        mime="text/plain",
                        use_container_width=True,
                    )
                else:
                    st.write("📊 共 **0** 条引用")
                    st.download_button(
                        label="📥 下载BibTeX",
                        data="",
                        file_name="literature.bib",
                        mime="text/plain",
                        use_container_width=True,
                        disabled=True,
                    )

        # 卡片3: Excel
        with col_card3:
            with st.container(border=True):
                st.markdown(
                    """
                <div style="text-align: center; padding: 10px;">
                    <span style="font-size: 40px;">📊</span>
                    <h4 style="margin: 10px 0;">Excel</h4>
                    <p style="color: gray; font-size: 12px;">表格数据</p>
                </div>
                """,
                    unsafe_allow_html=True,
                )
                if has_data:
                    st.write(f"📊 共 **{excel_count}** 条记录")
                    st.download_button(
                        label="📥 下载Excel",
                        data=excel_buffer,
                        file_name=f"{selected_db_name}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True,
                    )
                else:
                    st.write("📊 共 **0** 条记录")
                    st.download_button(
                        label="📥 下载Excel",
                        data=b"",
                        file_name="literature.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True,
                        disabled=True,
                    )

        st.divider()

        # ========== 知识库内容管理 ==========
        st.subheader("📚 知识库内容管理")

        # 初始化session state
        if "selected_papers_to_delete" not in st.session_state:
            st.session_state.selected_papers_to_delete = set()

        try:
            if os.path.exists(db_path):
                manager = LiteratureDatabaseManager(db_path)
                stats = manager.get_statistics()

                if stats["total_papers"] > 0:
                    # 统计信息
                    col_count1, col_count2, col_count3 = st.columns(3)
                    with col_count1:
                        st.metric("文献总数", stats["total_papers"])
                    with col_count2:
                        if stats.get("year_distribution"):
                            years = [
                                y
                                for y in stats["year_distribution"].keys()
                                if isinstance(y, int)
                            ]
                            if years:
                                st.metric("年份范围", f"{min(years)} - {max(years)}")
                            else:
                                st.metric("年份范围", "N/A")
                        else:
                            st.metric("年份范围", "N/A")
                    with col_count3:
                        if stats.get("top_journals"):
                            top_j = sorted(
                                stats["top_journals"].items(),
                                key=lambda x: x[1],
                                reverse=True,
                            )[:3]
                            st.write(
                                "Top期刊: "
                                + ", ".join(
                                    [
                                        f"{j[:15]}..." if len(j) > 15 else j
                                        for j, c in top_j
                                    ]
                                )
                            )
                        else:
                            st.write("Top期刊: 无")

                    # 搜索和筛选
                    col_search1, col_search2 = st.columns([3, 1])
                    with col_search1:
                        search_query = st.text_input(
                            "🔍 搜索文献",
                            placeholder="输入关键词搜索标题、作者、摘要...",
                        )
                    with col_search2:
                        all_years = sorted(
                            [
                                str(y)
                                for y in stats["year_distribution"].keys()
                                if isinstance(y, int)
                            ],
                            reverse=True,
                        )
                        year_filter = st.selectbox("年份筛选", ["全部"] + all_years)

                    # 获取文献列表
                    papers = (
                        manager.search(search_query, limit=1000)
                        if search_query
                        else manager.search("", limit=1000)
                    )
                    papers = [p for p in papers if p.year > 0]

                    if year_filter != "全部":
                        papers = [p for p in papers if p.year == int(year_filter)]

                    st.write(f"共找到 **{len(papers)}** 篇文献")

                    # 直接显示文献内容，不需要折叠
                    st.subheader("📋 查看文献内容")

                    if len(papers) > 0:
                        # 准备数据
                        papers_df = pd.DataFrame(
                            [
                                {
                                    "标题": paper.title,
                                    "作者": (paper.authors[:50] + "...")
                                    if paper.authors and len(paper.authors) > 50
                                    else (paper.authors or ""),
                                    "年份": paper.year,
                                    "期刊": (paper.journal[:30] + "...")
                                    if paper.journal and len(paper.journal) > 30
                                    else (paper.journal or ""),
                                }
                                for paper in papers
                            ]
                        )

                        # 显示表格
                        st.dataframe(
                            papers_df,
                            hide_index=True,
                            use_container_width=True,
                        )
                    else:
                        st.info("暂无文献")

                    st.divider()

                    # 统计信息
                    st.subheader("📊 统计信息")
                    st.write(f"当前文献库共 **{len(papers)}** 篇文献")

                else:
                    st.info("当前文献库为空")
            else:
                st.info("文献库不存在")

        except Exception as e:
            st.error(f"加载知识库失败: {str(e)}")

    # 清理临时文件
    if uploaded_literature_list and temp_lit_dir and os.path.exists(temp_lit_dir):
        try:
            shutil.rmtree(temp_lit_dir)
        except:
            pass

# ========== Tab 3: 一键写作（核心功能） ==========
with tab3:
    st.header("✍️ 一键写作")
    st.markdown(
        "上传研究背景文档（支持Word），系统自动解析文本、图表和表格，AI分析后供您确认，最后撰写完整论文"
    )

    # Initialize session state for document analysis
    if "doc_analysis_result" not in st.session_state:
        st.session_state.doc_analysis_result = None
    if "corrected_content" not in st.session_state:
        st.session_state.corrected_content = None

    col1, col2 = st.columns([1.3, 1])

    with col1:
        st.subheader("📤 上传研究文档（Word格式推荐）")
        st.markdown("上传包含研究背景、数据、图表的Word文档")

        uploaded_doc = st.file_uploader(
            "选择Word文档（.docx）",
            type=["docx"],
            help="Word文档可以包含文字、表格和截图图表，系统将自动解析",
            key="doc_uploader_tab3",
        )

        if uploaded_doc:
            st.success(f"已上传: {uploaded_doc.name}")

            # Save to temp file for analysis
            temp_doc_dir = tempfile.mkdtemp()
            doc_path = os.path.join(temp_doc_dir, uploaded_doc.name)
            with open(doc_path, "wb") as f:
                f.write(uploaded_doc.getbuffer())

            # Analyze button
            col_btn1, col_btn2 = st.columns([1, 2])
            with col_btn1:
                analyze_btn = st.button(
                    "🔍 解析文档并分析图表",
                    type="primary",
                    key="analyze_doc_btn",
                )

            # Progress indicator
            if "analyzing_doc" not in st.session_state:
                st.session_state.analyzing_doc = False

            if analyze_btn and not st.session_state.analyzing_doc:
                st.session_state.analyzing_doc = True
                st.rerun()

            # Display analysis results and allow review
            if st.session_state.get("analyzing_doc"):
                with st.spinner("正在解析文档和分析图表..."):
                    try:
                        from document_processor.word_analyzer import (
                            WordDocumentAnalyzer,
                            CorrectedContent,
                        )
                        from coordinator.multi_agent_coordinator import APIClient

                        # Create API client if configured
                        api_client = None
                        if api_url and api_key:
                            api_client = APIClient(api_url, api_key)

                        # Analyze document
                        analyzer = WordDocumentAnalyzer(api_client)
                        result = analyzer.analyze_document(
                            doc_path, analyze_images=bool(api_client)
                        )

                        st.session_state.doc_analysis_result = result
                        st.session_state.corrected_content = CorrectedContent()
                        st.session_state.analyzing_doc = False

                        st.success("文档解析完成！")

                    except Exception as e:
                        st.error(f"文档解析失败: {str(e)}")
                        st.session_state.analyzing_doc = False

        # Document preview and confirmation (moved here)
        if st.session_state.doc_analysis_result:
            result = st.session_state.doc_analysis_result
            st.success("✓ 文档已解析")

            # Initialize corrected content if needed
            if st.session_state.corrected_content is None:
                from document_processor.word_analyzer import CorrectedContent

                st.session_state.corrected_content = CorrectedContent()

            corrected = st.session_state.corrected_content

            # Summary of extracted elements
            st.markdown(f"""
            **文档内容摘要：**
            - 文本段落: {len([e for e in result.text_elements if e.element_type in ["Title", "Paragraph"]])} 个
            - 表格: {len(result.table_elements)} 个
            - 图片/图表: {len(result.image_elements)} 个
            """)

            # Extract text content for the paper
            text_parts = []
            for elem in result.text_elements:
                if elem.element_type == "Title":
                    text_parts.append(f"# {elem.text}")
                elif elem.element_type == "Table":
                    text_parts.append(f"\n[表格数据]\n{elem.text}")
                else:
                    text_parts.append(elem.text)
            corrected.text_content = "\n\n".join(text_parts)

            # Build results data from tables and images
            results_parts = []

            # Add table descriptions
            if result.table_elements:
                results_parts.append("【表格分析结果】")
                for table in result.table_elements:
                    if api_url and api_key:
                        from coordinator.multi_agent_coordinator import APIClient
                        from document_processor.word_analyzer import (
                            WordDocumentAnalyzer,
                        )

                        api_client_inner = APIClient(api_url, api_key)
                        analyzer_inner = WordDocumentAnalyzer(api_client_inner)
                        description = analyzer_inner.analyze_table_with_ai(table)
                        results_parts.append(
                            f"\n{table.caption or table.table_id}:\n{description}"
                        )
                        corrected.table_descriptions[table.table_id] = description
                    else:
                        results_parts.append(
                            f"\n{table.caption or table.table_id}: (需要API配置才能分析)"
                        )
                        corrected.table_descriptions[table.table_id] = (
                            "(需要API配置才能分析表格内容)"
                        )

            # Add image descriptions
            if result.image_elements:
                results_parts.append("\n【图表分析结果】")
                for img in result.image_elements:
                    if api_url and api_key:
                        with open(img.image_path, "rb") as f:
                            import base64

                            image_data = base64.b64encode(f.read()).decode()

                        prompt = """分析这张图表图片，请提供：
1. 图表类型（柱状图、折线图、散点图等）
2. 主要数据趋势
3. 关键数值或统计结果

请用简洁的中文描述。"""

                        messages = [
                            {
                                "role": "user",
                                "content": [
                                    {"type": "text", "text": prompt},
                                    {
                                        "type": "image_url",
                                        "image_url": {
                                            "url": f"data:image/png;base64,{image_data}"
                                        },
                                    },
                                ],
                            }
                        ]

                        from coordinator.multi_agent_coordinator import APIClient

                        api_client_inner = APIClient(api_url, api_key)
                        try:
                            response = api_client_inner.call_model(
                                model="gpt-4o", messages=messages, max_tokens=1000
                            )
                            img.description = response
                            results_parts.append(
                                f"\n{img.caption or img.image_id}:\n{response}"
                            )
                        except Exception as e:
                            img.description = f"分析失败: {str(e)}"
                            results_parts.append(
                                f"\n{img.caption or img.image_id}: 分析失败"
                            )
                    else:
                        results_parts.append(
                            f"\n{img.caption or img.image_id}: (需要API配置才能分析)"
                        )
                        img.description = "（需要配置API才能分析图表）"

            corrected.results_data = "\n".join(results_parts)

            # Show preview of confirmed data
            with st.expander("📄 查看已确认的研究数据", expanded=True):
                st.markdown(corrected.results_data)

    with col2:
        st.subheader("📋 上传文档说明")

        st.info("""
        **请将所有研究内容打包到一个Word文档中上传**
        """)

        # Download template button
        template_path = "research_content_template.md"
        if os.path.exists(template_path):
            with open(template_path, "r", encoding="utf-8") as f:
                template_content = f.read()
            st.download_button(
                label="📥 下载研究内容模板",
                data=template_content,
                file_name="research_content_template.md",
                mime="text/markdown",
                help="下载模板文档，按照模板结构整理您的研究内容",
                key="download_template",
            )
        else:
            st.caption("模板文件未找到")

        st.markdown("""
        **文档应包含以下内容：**

        1. **研究背景** - 主题、意义、研究现状
        2. **试验设计** - 目的、假设、分组、样本量
        3. **试验方法** - 数据收集、仪器、统计方法
        4. **试验地点与环境** - 地点、条件、周期
        5. **研究结果** - 数据表格、图表

        💡 **提示**：所有内容放入一个Word文档
        """)

        # Display document analysis status
        if st.session_state.doc_analysis_result:
            result = st.session_state.doc_analysis_result
            st.success("✓ 文档解析完成")

            # Initialize corrected content if needed
            if st.session_state.corrected_content is None:
                from document_processor.word_analyzer import CorrectedContent

                st.session_state.corrected_content = CorrectedContent()

            corrected = st.session_state.corrected_content

            # Summary of extracted elements
            st.markdown(f"""
            **文档内容摘要：**
            - 文本段落: {len([e for e in result.text_elements if e.element_type in ["Title", "Paragraph"]])} 个
            - 表格: {len(result.table_elements)} 个
            - 图片/图表: {len(result.image_elements)} 个
            """)

            # Extract text content for the paper
            text_parts = []
            for elem in result.text_elements:
                if elem.element_type == "Title":
                    text_parts.append(f"# {elem.text}")
                elif elem.element_type == "Table":
                    text_parts.append(f"\n[表格数据]\n{elem.text}")
                else:
                    text_parts.append(elem.text)
            corrected.text_content = "\n\n".join(text_parts)

            # Build results data from tables and images
            results_parts = []

            # Add table descriptions
            if result.table_elements:
                results_parts.append("【表格分析结果】")
                for table in result.table_elements:
                    if api_url and api_key:
                        from coordinator.multi_agent_coordinator import APIClient
                        from document_processor.word_analyzer import (
                            WordDocumentAnalyzer,
                        )

                        api_client_inner = APIClient(api_url, api_key)
                        analyzer_inner = WordDocumentAnalyzer(api_client_inner)
                        description = analyzer_inner.analyze_table_with_ai(table)
                        results_parts.append(
                            f"\n{table.caption or table.table_id}:\n{description}"
                        )
                        corrected.table_descriptions[table.table_id] = description
                    else:
                        results_parts.append(
                            f"\n{table.caption or table.table_id}: (需要API配置才能分析)"
                        )
                        corrected.table_descriptions[table.table_id] = (
                            "(需要API配置才能分析表格内容)"
                        )

            # Add image descriptions
            if result.image_elements:
                results_parts.append("\n【图表分析结果】")
                for img in result.image_elements:
                    if api_url and api_key:
                        with open(img.image_path, "rb") as f:
                            import base64

                            image_data = base64.b64encode(f.read()).decode()

                        prompt = """分析这张图表图片，请提供：
1. 图表类型（柱状图、折线图、散点图、饼图、热力图等）
2. 图表标题和坐标轴标签
3. 主要数据趋势和发现
4. 关键数值或统计结果
5. 图表的完整描述

请用简洁的中文描述。"""

                        messages = [
                            {
                                "role": "user",
                                "content": [
                                    {"type": "text", "text": prompt},
                                    {
                                        "type": "image_url",
                                        "image_url": {
                                            "url": f"data:image/png;base64,{image_data}"
                                        },
                                    },
                                ],
                            }
                        ]

                        from coordinator.multi_agent_coordinator import APIClient

                        api_client_inner = APIClient(api_url, api_key)
                        try:
                            response = api_client_inner.call_model(
                                model="gpt-4o", messages=messages, max_tokens=1000
                            )
                            img.description = response
                            results_parts.append(
                                f"\n{img.caption or img.image_id}:\n{response}"
                            )
                        except Exception as e:
                            img.description = f"分析失败: {str(e)}"
                            results_parts.append(
                                f"\n{img.caption or img.image_id}: 分析失败"
                            )
                    else:
                        results_parts.append(
                            f"\n{img.caption or img.image_id}: (需要API配置才能分析)"
                        )
                        img.description = "（需要配置API才能分析图表）"

            corrected.results_data = "\n".join(results_parts)

            # Show preview of confirmed data
            with st.expander("查看已确认的研究数据", expanded=True):
                st.markdown(corrected.results_data)

        else:
            st.info("请上传Word文档并点击解析")

    # Settings section (moved to bottom)
    st.divider()
    st.subheader("📁 输出设置")

    col_settings1, col_settings2 = st.columns(2)

    with col_settings1:
        output_dir = st.text_input(
            "📁 输出目录",
            value="output",
            key="output_dir_input_tab3",
            help="论文草稿的输出保存目录",
        )

    with col_settings2:
        if st.session_state.doc_analysis_result:
            st.success("✓ 研究数据已准备就绪")
        journal = st.text_input(
            "📚 目标期刊",
            value="Nature Communications",
            help="选择目标投稿期刊，AI将根据期刊风格调整论文格式",
            key="journal_input_tab3_main",
        )

    # 任务清单和模型选择（使用完整宽度）
    st.divider()
    col_task, col_model = st.columns([1.2, 1.5])

    with col_task:
        st.subheader("📋 任务清单")
        st.info("系统将自动完成以下步骤：")
        st.write("✅ 1. 分析范文风格（如有）")
        st.write("✅ 2. 导入文献数据库（如有）")
        st.write("✅ 3. 处理研究成果（如有）")
        st.write("✅ 4. 撰写引言（Introduction）")
        st.write("✅ 5. 撰写方法（Methods）")
        st.write("✅ 6. 撰写结果（Results）")
        st.write("✅ 7. 撰写讨论（Discussion）")
        st.write("✅ 8. 撰写摘要（Abstract）- 一级AI全局视角")
        st.write("✅ 9. 撰写结论（Conclusion）- 一级AI全局视角")
        st.write("✅ 10. **自动整合**所有章节")
        st.write("✅ 11. 质量检查与优化")

    with col_model:
        # Model selection for each section
        st.subheader("🤖 模型选择")
        st.markdown("为每个章节选择合适的模型")

        # Define available models with descriptions
        available_models = [
            ("GPT-4o", "GPT-4o - Balanced"),
            ("GPT-4o-mini", "GPT-4o-mini - Fast/Economical"),
            (
                "Claude-Sonnet-4.5",
                "Claude-Sonnet-4.5 - Critical thinking",
            ),
            (
                "Claude-Opus-4.5",
                "Claude-Opus-4.5 - Highest quality",
            ),
            ("Claude-Sonnet-4", "Claude-Sonnet-4 - Strong reasoning"),
            ("deepseek-chat", "DeepSeek-V3 - Cost-effective"),
        ]

        # Default model recommendations from coordinator config
        default_models = {
            "introduction": "GPT-4o",
            "methods": "GPT-4o",
            "results": "GPT-4o",
            "discussion": "Claude-Sonnet-4.5",
            "abstract": "GPT-4o",
            "conclusion": "Claude-Sonnet-4.5",
        }

        # Create columns for model selection
        col_model1, col_model2 = st.columns(2)

        # Model selections
        with col_model1:
            model_intro = st.selectbox(
                "引言",
                options=[m[0] for m in available_models],
                format_func=lambda x: next(
                    (m[1] for m in available_models if m[0] == x), x
                ),
                index=[m[0] for m in available_models].index(
                    default_models["introduction"]
                ),
                key="model_intro",
            )
            model_methods = st.selectbox(
                "方法",
                options=[m[0] for m in available_models],
                format_func=lambda x: next(
                    (m[1] for m in available_models if m[0] == x), x
                ),
                index=[m[0] for m in available_models].index(default_models["methods"]),
                key="model_methods",
            )
            model_results = st.selectbox(
                "结果",
                options=[m[0] for m in available_models],
                format_func=lambda x: next(
                    (m[1] for m in available_models if m[0] == x), x
                ),
                index=[m[0] for m in available_models].index(default_models["results"]),
                key="model_results",
            )

        with col_model2:
            model_discussion = st.selectbox(
                "讨论",
                options=[m[0] for m in available_models],
                format_func=lambda x: next(
                    (m[1] for m in available_models if m[0] == x), x
                ),
                index=[m[0] for m in available_models].index(
                    default_models["discussion"]
                ),
                key="model_discussion",
            )
            model_abstract = st.selectbox(
                "摘要",
                options=[m[0] for m in available_models],
                format_func=lambda x: next(
                    (m[1] for m in available_models if m[0] == x), x
                ),
                index=[m[0] for m in available_models].index(
                    default_models["abstract"]
                ),
                key="model_abstract",
            )
            model_conclusion = st.selectbox(
                "结论",
                options=[m[0] for m in available_models],
                format_func=lambda x: next(
                    (m[1] for m in available_models if m[0] == x), x
                ),
                index=[m[0] for m in available_models].index(
                    default_models["conclusion"]
                ),
                key="model_conclusion",
            )

        # Configuration summary
        st.caption(f"""
        **当前配置：**
        引言:{model_intro} | 方法:{model_methods} | 结果:{model_results} |
        讨论:{model_discussion} | 摘要:{model_abstract} | 结论:{model_conclusion}
        """)

    # Build model config dictionary
    model_config = {
        "introduction": model_intro,
        "methods": model_methods,
        "results": model_results,
        "discussion": model_discussion,
        "abstract": model_abstract,
        "conclusion": model_conclusion,
    }

    # 文献库选择（多选）- 放在最后
    st.divider()
    st.subheader("📚 选择文献库")
    output_dir_check = "output"
    if os.path.exists(output_dir_check):
        db_files_tab3 = [
            f.replace(".db", "")
            for f in os.listdir(output_dir_check)
            if f.endswith(".db")
        ]
    else:
        db_files_tab3 = []

    if db_files_tab3:
        selected_db_names_tab3 = st.multiselect(
            "选择要使用的文献库（可多选）",
            options=db_files_tab3,
            default=[],
            help="选中多个文献库，系统将合并所有库中的文献进行引用",
            key="db_selector_tab3",
        )
        if selected_db_names_tab3:
            # Calculate total papers from selected databases
            total_papers_count = 0
            paper_details = []
            try:
                from literature import LiteratureDatabaseManager

                for db_name in selected_db_names_tab3:
                    db_path = f"output/{db_name}.db"
                    if os.path.exists(db_path):
                        lit_manager = LiteratureDatabaseManager(db_path)
                        stats = lit_manager.get_statistics()
                        count = stats.get("total_papers", 0)
                        total_papers_count += count
                        paper_details.append(f"**{db_name}**: {count} 篇")
            except Exception:
                paper_details = ["(无法计算文献数量)"]

            # Display selection info
            st.success(
                f"已选择 {len(selected_db_names_tab3)} 个文献库，共 **{total_papers_count}** 篇文献"
            )
            with st.expander("查看各库文献数量"):
                for detail in paper_details:
                    st.write(detail)
        else:
            st.info("请选择要使用的文献库")
    else:
        selected_db_names_tab3 = []
        st.info("暂无文献库，请先在Tab 2导入文献")

    # Check for research data
    has_research_data = st.session_state.doc_analysis_result or uploaded_doc

    # ========== 风格选项管理 UI ==========
    st.subheader("⚙️ 写作章节配置")

    # 恢复固定选项
    if "style_analysis_options" not in st.session_state:
        st.session_state.style_analysis_options = {
            "selected_sections": [
                "abstract",
                "introduction",
                "methods",
                "results",
                "discussion",
                "conclusion",
            ],
            "fixed_options": [
                "abstract",
                "introduction",
                "methods",
                "results",
                "discussion",
                "conclusion",
            ],
        }

    # 所有可用的章节选项
    ALL_SECTION_OPTIONS = [
        ("abstract", "📄 摘要 (Abstract)"),
        ("introduction", "📝 引言 (Introduction)"),
        ("methods", "🔬 方法 (Methods)"),
        ("results", "📊 结果 (Results)"),
        ("discussion", "💬 讨论 (Discussion)"),
        ("conclusion", "✨ 结论 (Conclusion)"),
    ]

    # 恢复上次保存的选择
    current_selected = st.session_state.style_analysis_options.get(
        "selected_sections", []
    )

    # 使用多选框让用户选择要写作的章节
    col_opts1, col_opts2, col_opts3 = st.columns([2, 1, 1])

    with col_opts1:
        selected_sections = st.multiselect(
            "选择要生成的章节",
            options=[(v, l) for v, l in ALL_SECTION_OPTIONS],
            format_func=lambda x: x[1],
            default=[(v, l) for v, l in ALL_SECTION_OPTIONS if v in current_selected],
            key="section_multiselect",
            help="选择需要AI生成的论文章节",
        )

    with col_opts2:
        if st.button("✅ 全选", use_container_width=True):
            selected_sections = [(v, l) for v, l in ALL_SECTION_OPTIONS]
            st.session_state.style_analysis_options["selected_sections"] = [
                v for v, l in selected_sections
            ]
            st.rerun()

    with col_opts3:
        if st.button("🗑️ 清空", use_container_width=True):
            selected_sections = []
            st.session_state.style_analysis_options["selected_sections"] = []
            st.rerun()

    # 保存选择到session state
    st.session_state.style_analysis_options["selected_sections"] = [
        v for v, l in selected_sections
    ]

    # 显示已选择的章节标签
    if selected_sections:
        st.write("**已选择章节：**")
        cols = st.columns(6)
        for i, (v, l) in enumerate(selected_sections):
            with cols[i % 6]:
                # 添加固定/取消固定按钮
                is_fixed = v in st.session_state.style_analysis_options.get(
                    "fixed_options", []
                )
                fixed_label = "📌" if is_fixed else "🔓"
                if st.button(
                    f"{fixed_label} {l.split()[1]}",
                    key=f"fix_{v}",
                    help="点击切换固定状态",
                ):
                    fixed_list = st.session_state.style_analysis_options.get(
                        "fixed_options", []
                    )
                    if is_fixed:
                        fixed_list.remove(v)
                    else:
                        fixed_list.append(v)
                    st.session_state.style_analysis_options["fixed_options"] = (
                        fixed_list
                    )
                    st.rerun()
    else:
        st.warning("请至少选择一个章节")

    # 显示固定选项提示
    fixed_options = st.session_state.style_analysis_options.get("fixed_options", [])
    if fixed_options:
        fixed_labels = [dict(ALL_SECTION_OPTIONS).get(v, v) for v in fixed_options]
        st.caption(f"📌 固定选项: {', '.join(fixed_labels)}")

    if st.button("🚀 开始全自动写作", type="primary", use_container_width=True):
        if not has_research_data:
            st.warning("请先上传研究文档")
        elif not selected_sections:
            st.warning("请至少选择一个章节")
        else:
            # Create progress display
            progress_container = st.container()
            with progress_container:
                st.subheader("Writing Progress")

                progress_bar = st.progress(0)
                status_area = st.empty()
                log_area = st.empty()
                log_messages = []

                def progress_callback(step, total, section, progress):
                    """Progress callback for coordinator"""
                    status_area.text(f"步骤 {step}/{total}: 正在撰写 {section}...")
                    progress_bar.progress(progress)

                    section_names = {
                        "introduction": "引言",
                        "methods": "方法",
                        "results": "结果",
                        "discussion": "讨论",
                        "abstract": "摘要（一级AI全局视角）",
                        "conclusion": "结论（一级AI全局视角）",
                    }
                    log_messages.append(
                        f"✓ 正在撰写 {section_names.get(section, section)}..."
                    )
                    log_area.info("\n".join(log_messages[-5:]))

                # Step 1: Initialize
                status_area.text("正在初始化配置...")
                progress_bar.progress(5)
                log_area.info("开始论文写作流程...")

                try:
                    # Import coordinator
                    from coordinator import MultiAgentCoordinator
                    from integrator import DraftIntegrator

                    # Load detailed chapter-specific style guides
                    style_guide_dir = "output/style"
                    chapter_guides = {}

                    # Try to load individual chapter guides
                    guide_files = {
                        "abstract": "abstract_guide.md",
                        "introduction": "introduction_guide.md",
                        "methods": "methods_guide.md",
                        "results": "results_guide.md",
                        "discussion": "discussion_guide.md",
                        "conclusion": "conclusion_guide.md",
                    }

                    for chapter, filename in guide_files.items():
                        guide_path = os.path.join(style_guide_dir, filename)
                        if os.path.exists(guide_path):
                            with open(guide_path, "r", encoding="utf-8") as f:
                                chapter_guides[chapter] = f.read()
                        else:
                            chapter_guides[chapter] = (
                                f"# {chapter.title()} Writing Guide\n\nNo specific guide available for this chapter."
                            )

                    # Create comprehensive style guide by combining all chapter guides
                    comprehensive_guide = f"""# Comprehensive Journal Style Guide

## Overview
This guide provides detailed writing instructions for each section of papers published in the target journal.

## Section-Specific Guidelines

"""

                    for chapter, content in chapter_guides.items():
                        comprehensive_guide += (
                            f"\n## {chapter.title()} Section\n{content}\n"
                        )

                    # Add general style information from summary if available
                    summary_path = os.path.join(style_guide_dir, "style_summary.md")
                    if os.path.exists(summary_path):
                        with open(summary_path, "r", encoding="utf-8") as f:
                            comprehensive_guide += (
                                f"\n## General Style Summary\n{f.read()}\n"
                            )

                    # Use comprehensive guide as style_guide content
                    style_guide_content = comprehensive_guide

                    # Load background content from document analysis
                    background_content = ""
                    if st.session_state.doc_analysis_result:
                        # Use extracted text from Word document
                        result = st.session_state.doc_analysis_result
                        text_parts = []
                        for elem in result.text_elements:
                            if elem.element_type == "Title":
                                text_parts.append(f"# {elem.text}")
                            elif elem.element_type == "Table":
                                text_parts.append(f"\n[表格数据]\n{elem.text}")
                            else:
                                text_parts.append(elem.text)
                        background_content = "\n\n".join(text_parts)
                        log_messages.append("✓ 已使用Word文档解析的文本内容")

                    # Fallback: use default content
                    if not background_content:
                        background_content = "请根据提供的研究背景撰写内容。"
                        log_messages.append("⚠ 未检测到文档内容，将使用默认背景")

                    # Load results data from corrected content or file
                    results_data = ""

                    # Priority 1: Use corrected content from document analysis
                    if st.session_state.get("corrected_content"):
                        corrected = st.session_state.corrected_content
                        results_parts = []

                        # Add table descriptions
                        if corrected.table_descriptions:
                            results_parts.append("【表格分析结果】")
                            for table_id, desc in corrected.table_descriptions.items():
                                results_parts.append(f"\n{table_id}:\n{desc}")

                        # Add image descriptions (from session state)
                        if st.session_state.doc_analysis_result:
                            for (
                                img
                            ) in st.session_state.doc_analysis_result.image_elements:
                                results_parts.append(
                                    f"\n{img.image_id} (图表):\n{img.description}"
                                )

                        if results_parts:
                            results_data = "\n".join(results_parts)
                            log_messages.append("✓ 已使用修正后的图表/表格分析结果")

                    # Step 2: Create coordinator with user-provided API config
                    progress_bar.progress(10)
                    status_area.text("正在初始化AI协调器...")

                    # Validate API configuration
                    if not api_url or not api_key:
                        st.error("请在侧边栏输入API地址和API Key")
                        raise Exception("缺少API配置")

                    coordinator = MultiAgentCoordinator(
                        base_url=api_url, api_key=api_key, model_config=model_config
                    )

                    # Load literature from multiple databases
                    literature_papers = []
                    if selected_db_names_tab3:
                        try:
                            from literature import LiteratureDatabaseManager

                            total_papers = 0
                            for db_name in selected_db_names_tab3:
                                db_path = f"output/{db_name}.db"
                                if os.path.exists(db_path):
                                    lit_manager = LiteratureDatabaseManager(db_path)
                                    papers = lit_manager.search("", limit=100)
                                    literature_papers.extend(papers)
                                    total_papers += len(papers)
                                    log_messages.append(
                                        f"✓ 从 {db_name} 加载了 {len(papers)} 篇文献"
                                    )
                            log_messages.append(
                                f"✓ 共加载 {total_papers} 篇文献用于引用"
                            )
                        except Exception as e:
                            st.warning(f"加载文献数据库失败: {e}")
                    else:
                        st.info("未选择文献库，将不使用文献引用功能")

                    # Get citation style from style analysis if available
                    citation_style = {
                        "citation_type": "author-year",
                        "reference_format": "nature",
                    }
                    style_summary_path = os.path.join(
                        style_guide_dir, "style_summary.md"
                    )
                    if os.path.exists(style_summary_path):
                        try:
                            import json

                            report_path = os.path.join(
                                style_guide_dir, "journal_style_report.json"
                            )
                            if os.path.exists(report_path):
                                with open(report_path, "r", encoding="utf-8") as f:
                                    report_data = json.load(f)
                                    if "citation_style" in report_data:
                                        citation_style = report_data["citation_style"]
                                        log_messages.append(
                                            f"✓ 已加载引用风格: {citation_style.get('citation_type', 'author-year')}"
                                        )
                        except Exception as e:
                            log_messages.append(f"⚠ 无法加载引用风格配置，使用默认值")

                    # Prepare context
                    context = {
                        "background": background_content,
                        "style_guide": style_guide_content,
                        "citation_style": citation_style,
                        "literature": literature_papers,
                        "results_data": results_data,
                        "target_journal": journal,
                    }

                    # Get selected sections from session state
                    selected_sections = st.session_state.style_analysis_options.get(
                        "selected_sections", None
                    )

                    # Step 3-8: Run coordinator workflow
                    status_area.text("正在运行AI写作流程...")
                    progress_bar.progress(15)

                    results = coordinator.run_workflow(
                        context=context,
                        progress_callback=progress_callback,
                        sections=selected_sections,
                    )

                    # Save sections
                    os.makedirs(os.path.join(output_dir, "sections"), exist_ok=True)
                    for section_name, result in results.items():
                        section_path = os.path.join(
                            output_dir, "sections", f"{section_name}.md"
                        )
                        with open(section_path, "w", encoding="utf-8") as f:
                            f.write(result.content)
                        log_messages.append(
                            f"✓ Saved {section_name}: {result.word_count} words"
                        )

                    progress_bar.progress(95)
                    status_area.text("Integrating all sections...")

                    # Step 9: Integrate sections
                    sections_dict = {
                        "introduction": os.path.join(
                            output_dir, "sections", "introduction.md"
                        ),
                        "methods": os.path.join(output_dir, "sections", "methods.md"),
                        "results": os.path.join(output_dir, "sections", "results.md"),
                        "discussion": os.path.join(
                            output_dir, "sections", "discussion.md"
                        ),
                    }

                    integrator = DraftIntegrator()
                    sections_content = integrator.collect_sections(sections_dict)
                    draft, report = integrator.integrate(sections_content)

                    # Save final draft
                    os.makedirs(os.path.join(output_dir, "final"), exist_ok=True)
                    final_draft_path = os.path.join(
                        output_dir, "final", "final_draft.md"
                    )
                    with open(final_draft_path, "w", encoding="utf-8") as f:
                        f.write(draft)

                    # Save report
                    report_path = os.path.join(output_dir, "final", "draft_report.json")
                    integrator.save_report(report, report_path)

                    # Step 10: Quality check
                    progress_bar.progress(100)
                    status_area.text("质量检查完成！")

                    # Show success message
                    st.success(
                        f"""
                        **论文写作完成！**

                        **输入内容：**
                        - 研究文档: {uploaded_doc.name if uploaded_doc else "使用已解析文档"}

                        **生成的文件：**
                        - `output/sections/abstract.md` - 摘要（一级AI全局视角）
                        - `output/sections/introduction.md` - 引言
                        - `output/sections/methods.md` - 方法
                        - `output/sections/results.md` - 结果
                        - `output/sections/discussion.md` - 讨论
                        - `output/sections/conclusion.md` - 结论（一级AI全局视角）
                        - `output/final/final_draft.md` - 整合后的完整草稿

                        **质量报告：**
                        - 总字数: {report.total_words}
                        - 质量评分: {report.overall_quality_score:.2f}
                        - 发现问题: {report.consistency_report.get("total_issues", 0)}
                        """
                    )

                    # Show file list
                    with st.expander("查看生成的文件"):
                        sections_dir = os.path.join(output_dir, "sections")
                        final_dir = os.path.join(output_dir, "final")

                        if os.path.exists(sections_dir):
                            st.write("**各章节：**")
                            for f in sorted(os.listdir(sections_dir)):
                                st.write(f"  📄 {f}")

                        if os.path.exists(final_dir):
                            st.write("**最终草稿：**")
                            for f in os.listdir(final_dir):
                                st.write(f"  📄 {f}")

                except Exception as e:
                    st.error(f"写作失败: {str(e)}")
                    import traceback

                    with st.expander("错误详情"):
                        st.code(traceback.format_exc())

        # Note: 临时文件会在会话结束时自动清理

        # 清理临时文件
        st.info("💡 临时文件会在会话结束时自动清理")

# ========== Tab 4: 了解更多 ==========
with tab4:
    st.header("💡 项目架构与AI模型")
    st.markdown("了解整个论文写作系统的工作流程和每个阶段使用的AI模型")

    # 工作流程图
    st.subheader("📊 完整工作流程")

    workflow = """
    ```
    ┌─────────────────────────────────────────────────────────────────────────┐
    │                        论文写作助手 - 系统架构                            │
    └─────────────────────────────────────────────────────────────────────────┘
    
    输入层                          处理层                           输出层
    ┌──────────┐          ┌────────────────────────┐          ┌──────────┐
    │          │          │                        │          │          │
    │  研究背景 │────────▶│  1. 背景解析器          │          │          │
    │  (PDF/   │          │  AI: Claude-Sonnet-4   │          │  摘要    │
    │   Word)  │          │  提取研究主题/方法/数据 │          │  (一级AI) │
    │          │          │                        │          │          │
    └──────────┘          └────────────────────────┘          │  引言    │
           │                        │                        │DeepSeek  │
           │                        ▼                        │          │
    ┌──────────┐          ┌────────────────────────┐          │          │
    │          │          │  2. 文献数据库          │          │  方法    │
    │  文献Excel│────────▶│  AI: Claude-Sonnet-4   │────────▶│Claude-   │
    │  (WOS)   │          │  精准识别每个单元格     │          │  Sonnet  │
    │          │          │                        │          │          │
    └──────────┘          └────────────────────────┘          │          │
           │                        │                        │  结果    │
           │                        ▼                        │GPT-4o    │
    ┌──────────┐          ┌────────────────────────┐          │          │
    │          │          │  3. 风格分析器          │          │          │
    │  范文PDF │────────▶│  AI: GPT-4o            │────────▶│  讨论    │
    │          │          │  提取词汇/时态/过渡词   │          │Claude-   │
    │          │          │                        │          │  3.5     │
    └──────────┘          └────────────────────────┘          │          │
           │                        │                        │          │
           │                        ▼                        │  结论    │
    ┌──────────┐          ┌────────────────────────┐          │  (一级AI) │
    │          │          │  4. 协调器(Coordinator) │          │          │
    │          │          │  管理6个写作Agent       │          │ 完整论文 │
    │          │◀─────────│  ★一级AI全局视角★     │────────▶│  (最终   │
    │          │          │                        │          │   草稿)  │
    │          │          └────────────────────────┘          │          │
    │          │                        │                    │          │
    │          │          ┌────────────────────────┐          │          │
    │          │          │  5. 草稿整合器          │          │          │
    │          │◀─────────│  AI: Claude-Sonnet-4   │────────▶│          │
    │          │          │  检查一致性/增强过渡   │          │          │
    │          │          │                        │          │          │
    └──────────┘          └────────────────────────┘          └──────────┘
    
    注: 摘要(Abstract)和结论(Conclusion)由一级AI(Coordinator)根据全文全局视角撰写
    ```
    """
    st.markdown(workflow)

    # AI模型使用详情
    st.subheader("🤖 各阶段AI模型详情")

    ai_details = """
    | 阶段 | 任务 | AI模型 | 提供商 | 成本/1K tokens | 选择理由 |
    |------|------|--------|--------|---------------|----------|
    | 风格分析 | 提取词汇/时态/过渡词 | **GPT-4o** | OpenAI | $0.02 | 复杂模式识别最强 |
    | 文献导入 | 精准识别Excel单元格 | **Claude-Sonnet-4** | Anthropic | $0.018 | 结构化提取最准 |
    | 引言写作 | 创意背景叙述 | **DeepSeek-Chat** | DeepSeek | $0.00042 | 性价比最高 |
    | 方法写作 | 技术文档撰写 | **Claude-Sonnet-4** | Anthropic | $0.018 | 技术术语最精确 |
    | 结果写作 | 数据描述/统计 | **GPT-4o** | OpenAI | $0.02 | 数值推理最强 |
    | 讨论写作 | 论证/综合分析 | **Claude-3.5-Sonnet** | Anthropic | $0.018 | 论证能力最强 |
    | ⭐ 摘要 | 全局总结（根据全文） | **Claude-Sonnet-4** | Anthropic | $0.018 | 一级AI全局视角 |
    | ⭐ 结论 | 综合分析（根据全文） | **Claude-Sonnet-4** | Anthropic | $0.018 | 一级AI全局视角 |
    | 草稿整合 | 一致性检查/过渡 | **Claude-Sonnet-4** | Anthropic | $0.018 | 质量检查最仔细 |
    
    ⭐ 表示由一级AI（Coordinator）基于全局视角撰写
    """
    st.markdown(ai_details)

    # 成本对比
    st.subheader("💰 成本优化策略")

    cost_info = """
    ### 为什么这样选择？
    
    - **DeepSeek** (写作任务): 价格仅为GPT-4o的1/50，但写作质量相当
    - **Claude** (分析任务): 结构化理解能力最强，适合提取和分析
    - **GPT-4o** (数值任务): 推理能力最强，适合数据描述
    
    ### 成本对比
    
    | 方案 | 每篇论文成本 | 10篇成本 |
    |------|------------|---------|
    | 全部使用GPT-4o | ~$0.50 | $5.00 |
    | 全部使用Claude | ~$0.40 | $4.00 |
    | **我们的混合方案** | **~$0.07** | **~$0.70** |
    
    **节省约85%成本！**
    """
    st.markdown(cost_info)

    # 技术栈
    st.subheader("🛠️ 技术栈")

    tech_stack = """
    ### 前端
    - **Streamlit** - 网页界面
    
    ### 后端
    - **Python** - 主要开发语言
    - **SpaCy** - NLP文本处理
    - **NLTK** - 自然语言处理
    
    ### 文档处理
    - **pdfplumber** - PDF解析
    - **python-docx** - Word解析
    - **openpyxl** - Excel解析
    
    ### API代理
    - 本地代理: `http://127.0.0.1:13148/v1`
    - 支持: OpenAI, Anthropic, DeepSeek等多种模型
    """
    st.markdown(tech_stack)

    # 使用流程
    st.subheader("📖 使用流程")

    usage_flow = """
    ### 三步完成论文写作
    
    1. **上传文件**
        - 研究背景 (PDF/Word/Markdown)
        - 研究成果 (Excel/图片/描述) - 可选
        - 文献数据库 (Excel) - 可选
        - 范文样本 (PDF) - 可选
    
    2. **点击开始**
       - 系统自动完成所有步骤
       - 无需手动干预
    
    3. **下载论文**
       - 各章节独立文件（摘要/引言/方法/结果/讨论/结论）
       - 整合后的完整草稿
    
    ### 生成的全部章节
    1. **摘要 (Abstract)** - 一级AI全局视角总结
    2. **引言 (Introduction)** - DeepSeek撰写
    3. **方法 (Methods)** - Claude-Sonnet-4撰写
    4. **结果 (Results)** - GPT-4o撰写
    5. **讨论 (Discussion)** - Claude-3.5-Sonnet撰写
    6. **结论 (Conclusion)** - 一级AI全局视角总结
    
    ### 注意事项
    - 确保API代理正在运行
    - API Key已预填在侧边栏
    - 可选步骤不影响核心功能
    """
    st.markdown(usage_flow)

    # 摘要和结论为什么重要
    st.subheader("📝 为什么摘要和结论由一级AI撰写？")

    abstract_reason = """
    ### 一级AI（Coordinator）的全局视角优势
    
    **传统做法：**
    - 各章节由不同AI独立撰写
    - 摘要和结论容易与正文脱节
    - 难以形成统一的论述主线
    
    **我们的方案：**
    - 一级AI在所有章节完成后撰写摘要和结论
    - 具有完整的全文上下文
    - 能准确总结研究目的、方法、主要发现和贡献
    - 确保摘要与正文高度一致
    
    **Claude-Sonnet-4的优势：**
    - 200K token上下文窗口
    - 强大的长文本理解和综合能力
    - 能够从全局角度提炼关键信息
    - 生成结构清晰、重点突出的摘要和结论
    """
    st.markdown(abstract_reason)

# 底部信息
st.divider()
st.markdown(
    """
<div style='text-align: center; color: gray;'>
    <p>📝 论文写作助手 | 基于多代理AI系统</p>
    <p>只需上传背景文件，点击"开始写作"即可自动完成全文</p>
</div>
""",
    unsafe_allow_html=True,
)
