"""
论文写作辅助系统 - CLI入口
"""

import json
import sys
from pathlib import Path
from typing import Optional

import click
from rich import print as rprint
from rich.panel import Panel
from rich.table import Table


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """论文写作辅助系统 - 基于多AI Agent协作的论文写作工具"""
    pass


@cli.command()
@click.argument("papers_dir", type=click.Path(exists=True, file_okay=False))
@click.argument("output_dir", type=click.Path())
@click.option("--journal", "-j", default="Target Journal", help="期刊名称")
def analyze(papers_dir: str, output_dir: str, journal: str):
    """分析目标期刊的写作风格"""
    from src import analyze_journal_style

    rprint(f"[bold]分析期刊风格...[/bold]")
    rprint(f"论文目录: {papers_dir}")
    rprint(f"输出目录: {output_dir}")
    rprint(f"期刊名称: {journal}")

    try:
        result = analyze_journal_style(papers_dir, output_dir, journal)

        rprint(Panel.fit("[green]分析完成！[/green]", title="成功"))

        table = Table(title="输出文件")
        table.add_column("文件")
        table.add_column("路径")

        for key, path in result.get("guides", {}).items():
            table.add_row(key, path)
        table.add_row("报告", result.get("report", ""))
        table.add_row("摘要", result.get("summary", ""))

        rprint(table)

    except Exception as e:
        rprint(Panel.fit(f"[red]错误: {e}[/red]", title="失败"))
        sys.exit(1)


@cli.command()
@click.argument("excel_path", type=click.Path(exists=True))
@click.argument("db_path", default="data/literature.db")
def import_literature(excel_path: str, db_path: str):
    """从Web of Science导出的Excel文件导入文献库"""
    from src import create_literature_database

    rprint(f"[bold]导入文献库...[/bold]")
    rprint(f"Excel文件: {excel_path}")
    rprint(f"数据库路径: {db_path}")

    try:
        manager = create_literature_database(excel_path, db_path)
        stats = manager.get_statistics()

        rprint(Panel.fit("[green]导入完成！[/green]", title="成功"))

        table = Table(title="数据库统计")
        table.add_column("指标")
        table.add_column("值")

        table.add_row("总论文数", str(stats.get("total_papers", 0)))

        for journal, count in list(stats.get("top_journals", {}).items())[:5]:
            table.add_row(f"期刊: {journal[:30]}...", str(count))

        rprint(table)

    except Exception as e:
        rprint(Panel.fit(f"[red]错误: {e}[/red]", title="失败"))
        sys.exit(1)


@cli.command()
@click.argument("background_path", type=click.Path(exists=True))
@click.argument("style_guide_path", type=click.Path(exists=True))
@click.argument("literature_db_path", type=click.Path(exists=True))
@click.option("--output", "-o", default="output/sections/", help="输出目录")
def write(
    background_path: str, style_guide_path: str, literature_db_path: str, output: str
):
    """使用多Agent系统撰写论文各章节"""
    from src import run_coordinator

    rprint(f"[bold]开始论文写作...[/bold]")

    try:
        report = run_coordinator(
            background_path=background_path,
            style_guide_path=style_guide_path,
            literature_db_path=literature_db_path,
        )

        rprint(Panel.fit("[green]写作完成！[/green]", title="成功"))

        table = Table(title="执行结果")
        table.add_column("章节")
        table.add_column("字数")
        table.add_column("质量分")
        table.add_column("状态")

        for section, result in report.get("results", {}).items():
            table.add_row(
                section,
                str(result.get("word_count", 0)),
                str(result.get("quality_score", 0)),
                result.get("status", "unknown"),
            )

        rprint(table)

        rprint(f"\n[bold]元数据:[/bold]")
        rprint(
            f"  总耗时: {report.get('metadata', {}).get('total_duration_seconds', 0)}秒"
        )
        rprint(
            f"  平均质量分: {report.get('metadata', {}).get('average_quality_score', 0)}"
        )

    except Exception as e:
        rprint(Panel.fit(f"[red]错误: {e}[/red]", title="失败"))
        sys.exit(1)


@cli.command()
@click.argument("sections_dir", type=click.Path(exists=True, file_okay=False))
@click.argument("output_file", type=click.Path())
def integrate(sections_dir: str, output_file: str):
    """整合各章节草稿"""
    from src import integrate_sections

    rprint(f"[bold]整合草稿...[/bold]")

    try:
        # 收集章节文件
        section_files = {}
        for section in ["introduction", "methods", "results", "discussion"]:
            file_path = Path(sections_dir) / f"{section}.md"
            if file_path.exists():
                section_files[section] = str(file_path)

        if not section_files:
            rprint("[yellow]警告: 未找到任何章节文件[/yellow]")
            return

        draft, result = integrate_sections(section_files, output_file)

        rprint(Panel.fit("[green]整合完成！[/green]", title="成功"))

        rprint(f"\n[bold]结果:[/bold]")
        rprint(f"  草稿路径: {result['draft_path']}")
        rprint(f"  字数: {result['total_words']}")
        rprint(f"  质量分: {result['quality_score']}")
        rprint(f"  报告: {result['report_path']}")

        if result["issues_count"] > 0:
            rprint(f"[yellow]发现 {result['issues_count']} 个问题需审查[/yellow]")

    except Exception as e:
        rprint(Panel.fit(f"[red]错误: {e}[/red]", title="失败"))
        sys.exit(1)


@cli.command()
@click.argument("input_dir", type=click.Path(exists=True, file_okay=False))
@click.argument("output_dir", type=click.Path())
@click.option("--journal", "-j", default="Target Journal", help="期刊名称")
def run(input_dir: str, output_dir: str, journal: str):
    """运行完整流程: 分析风格 -> 导入文献 -> 撰写论文 -> 整合草稿"""
    from src import (
        analyze_journal_style,
        create_literature_database,
        run_coordinator,
        integrate_sections,
    )

    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    rprint(
        Panel.fit(
            f"[bold]开始完整流程...[/bold]\n输入目录: {input_dir}\n输出目录: {output_dir}",
            title="论文写作辅助系统",
        )
    )

    # Step 1: 分析期刊风格
    rprint("\n[bold]Step 1: 分析期刊风格...[/bold]")
    papers_dir = input_path / "sample_papers"
    style_output = output_path / "style"
    if papers_dir.exists():
        result = analyze_journal_style(str(papers_dir), str(style_output), journal)
        rprint(f"  ✓ 风格分析完成")
    else:
        rprint(f"  ⚠ 未找到范文目录: {papers_dir}")

    # Step 2: 导入文献库
    rprint("\n[bold]Step 2: 导入文献库...[/bold]")
    literature_file = input_path / "literature.xlsx"
    db_path = output_path / "literature.db"
    if literature_file.exists():
        manager = create_literature_database(str(literature_file), str(db_path))
        rprint(f"  ✓ 导入 {manager.get_statistics().get('total_papers', 0)} 篇文献")
    else:
        rprint(f"  ⚠ 未找到文献文件: {literature_file}")

    # Step 3: 撰写论文
    rprint("\n[bold]Step 3: 撰写论文...[/bold]")
    background_file = input_path / "background.md"
    sections_output = output_path / "sections"
    if (
        background_file.exists()
        and (style_output / "journal_style_report.json").exists()
    ):
        report = run_coordinator(
            background_path=str(background_file),
            style_guide_path=str(style_output / "introduction_guide.md"),
            literature_db_path=str(db_path),
        )
        rprint(f"  ✓ 撰写完成")
        rprint(f"    - 引言: {report['results']['introduction']['word_count']}字")
        rprint(f"    - 方法: {report['results']['methods']['word_count']}字")
        rprint(f"    - 结果: {report['results']['results']['word_count']}字")
        rprint(f"    - 讨论: {report['results']['discussion']['word_count']}字")
    else:
        rprint(f"  ⚠ 缺少必要文件")

    # Step 4: 整合草稿
    rprint("\n[bold]Step 4: 整合草稿...[/bold]")
    section_files = {
        "introduction": str(sections_output / "introduction.md"),
        "methods": str(sections_output / "methods.md"),
        "results": str(sections_output / "results.md"),
        "discussion": str(sections_output / "discussion.md"),
    }

    # 检查文件是否存在
    for section, path in section_files.items():
        if not Path(path).exists():
            section_files[section] = str(sections_output / f"{section}.txt")

    draft_path = output_path / "final_draft.md"
    draft, result = integrate_sections(section_files, str(draft_path))
    rprint(f"  ✓ 整合完成")
    rprint(f"    - 总字数: {result['total_words']}")
    rprint(f"    - 质量分: {result['quality_score']}")

    # 总结
    rprint(
        Panel.fit(
            f"[bold]流程完成！[/bold]\n\n"
            f"输出文件:\n"
            f"  - 风格分析: {style_output}/\n"
            f"  - 文献库: {db_path}\n"
            f"  - 章节草稿: {sections_output}/\n"
            f"  - 最终草稿: {draft_path}",
            title="完成",
        )
    )


def main():
    """主入口"""
    cli()


if __name__ == "__main__":
    main()
