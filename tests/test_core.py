"""
测试模块
"""

import pytest
import sys
from pathlib import Path

# 添加src目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestConfig:
    """配置测试"""

    def test_config_load(self):
        """测试配置加载"""
        from src.config import Config

        config = Config("config/config.yaml")
        assert config is not None
        assert config.api_key == ""  # 未配置时为空
        assert config.model == "claude-3-opus-20240229"

    def test_config_get(self):
        """测试配置获取"""
        from src.config import Config

        config = Config("config/config.yaml")
        assert config.get("api.model") == "claude-3-opus-20240229"
        assert config.get("nonexistent.key", "default") == "default"


class TestJournalStyleAnalyzer:
    """期刊风格分析器测试"""

    def test_analyzer_init(self):
        """测试分析器初始化"""
        from src.analyzer import JournalStyleAnalyzer

        analyzer = JournalStyleAnalyzer()
        assert analyzer is not None
        assert analyzer.language == "english"

    def test_transition_words(self):
        """测试过渡词分类"""
        from src.analyzer import JournalStyleAnalyzer

        analyzer = JournalStyleAnalyzer()
        assert "sequential" in analyzer.TRANSITION_CATEGORIES
        assert "contrastive" in analyzer.TRANSITION_CATEGORIES
        assert "however" in analyzer.TRANSITION_CATEGORIES["contrastive"]


class TestLiteratureDB:
    """文献数据库测试"""

    def test_db_manager_init(self, tmp_path):
        """测试数据库管理器初始化"""
        from src.literature import LiteratureDatabaseManager

        db_path = str(tmp_path / "test_literature.db")
        manager = LiteratureDatabaseManager(db_path)

        assert manager.db_path.exists()
        assert manager is not None

    def test_paper_creation(self):
        """测试论文数据类"""
        from src.literature import Paper

        paper = Paper(
            id=1,
            title="Test Paper",
            authors="Test Author",
            journal="Test Journal",
            year=2024,
            doi="10.1000/test",
        )

        assert paper.title == "Test Paper"
        assert paper.year == 2024
        assert paper.doi == "10.1000/test"

    def test_citation_formatting(self, tmp_path):
        """测试引用格式化"""
        from src.literature import LiteratureDatabaseManager, Paper

        db_path = str(tmp_path / "test_citations.db")
        manager = LiteratureDatabaseManager(db_path)

        paper = Paper(
            id=1,
            title="Test",
            authors="Zhang, Y. and Wang, L.",
            year=2024,
            journal="Test",
        )

        # Author-year格式
        citation = manager.format_citation(paper, "author-year")
        assert "2024" in citation

        # Numbered格式
        citation = manager.format_citation(paper, "numbered")
        assert "[1]" in citation


class TestCoordinator:
    """协调器测试"""

    def test_coordinator_init(self):
        """测试协调器初始化"""
        from src.coordinator import MultiAgentCoordinator

        coordinator = MultiAgentCoordinator("config/config.yaml")
        assert coordinator is not None
        assert "introduction" in coordinator.agent_registry
        assert "methods" in coordinator.agent_registry
        assert "results" in coordinator.agent_registry
        assert "discussion" in coordinator.agent_registry

    def test_task_creation(self):
        """测试任务创建"""
        from src.coordinator import MultiAgentCoordinator, AgentStatus

        coordinator = MultiAgentCoordinator("config/config.yaml")
        tasks = coordinator.create_tasks(
            ["introduction", "methods", "results", "discussion"]
        )

        assert len(tasks) == 4
        assert tasks[0].agent_type == "introduction"
        assert tasks[0].status == AgentStatus.PENDING

    def test_quality_score_calculation(self):
        """测试质量分数计算"""
        from src.coordinator import MultiAgentCoordinator

        coordinator = MultiAgentCoordinator("config/config.yaml")

        # 测试不同内容的质量分数
        good_content = "## Introduction\n\nResearch background...\nOur study (Zhang et al., 2023) found that..."
        bad_content = "Intro"

        good_score = coordinator._calculate_quality_score(good_content)
        bad_score = coordinator._calculate_quality_score(bad_content)

        assert good_score > bad_score
        assert 0 <= good_score <= 1
        assert 0 <= bad_score <= 1


class TestIntegrator:
    """整合器测试"""

    def test_integrator_init(self):
        """测试整合器初始化"""
        from src.integrator import DraftIntegrator

        integrator = DraftIntegrator("config/config.yaml")
        assert integrator is not None

    def test_transition_words(self):
        """测试过渡词"""
        from src.integrator import DraftIntegrator

        integrator = DraftIntegrator()
        assert "sequential" in integrator.TRANSITION_WORDS
        assert "contrastive" in integrator.TRANSITION_WORDS
        assert "however" in integrator.TRANSITION_WORDS["contrastive"]

    def test_section_collection(self, tmp_path):
        """测试章节收集"""
        from src.integrator import DraftIntegrator

        # 创建测试文件
        intro_file = tmp_path / "introduction.md"
        intro_file.write_text("## Introduction\n\nTest content...")

        integrator = DraftIntegrator()
        sections = integrator.collect_sections(
            {
                "introduction": str(intro_file),
                "methods": str(tmp_path / "methods.md"),
                "results": str(tmp_path / "results.md"),
                "discussion": str(tmp_path / "discussion.md"),
            }
        )

        assert "introduction" in sections
        assert "Test content" in sections["introduction"]

    def test_completeness_validation(self):
        """测试完整性验证"""
        from src.integrator import DraftIntegrator

        integrator = DraftIntegrator()

        sections = {
            "introduction": "Introduction content...",
            "methods": "Methods content...",
            "results": "Results content...",
            "discussion": "Discussion content...",
        }

        result = integrator.validate_completeness(sections)

        assert result["is_complete"] == True
        assert len(result["sections_present"]) == 4
        assert len(result["sections_missing"]) == 0

    def test_data_consistency_check(self):
        """测试数据一致性检查"""
        from src.integrator import DraftIntegrator

        integrator = DraftIntegrator()

        sections = {
            "introduction": "We collected n=100 samples...",
            "methods": "A total of n=100 samples were collected...",
            "results": "Analysis of n=98 samples showed...",
        }

        issues, stats = integrator.check_data_consistency(sections)

        # 应该检测到样本量不一致
        sample_issues = [i for i in issues if i.type == "numerical"]
        assert len(sample_issues) >= 1


class TestCLI:
    """CLI测试"""

    def test_cli_import(self):
        """测试CLI导入"""
        from src.main import cli

        assert cli is not None

    def test_cli_commands(self):
        """测试CLI命令存在"""
        from src.main import cli

        # 检查命令组包含子命令
        commands = cli.commands
        assert "analyze" in commands
        assert "import_literature" in commands
        assert "write" in commands
        assert "integrate" in commands
        assert "run" in commands


# Fixtures
@pytest.fixture
def sample_paper(tmp_path):
    """示例论文文件"""
    content = """# Sample Paper

## Introduction

This study investigates the effects of climate change on crop yields. Previous research (Smith et al., 2020) has shown significant impacts. However, few studies have examined regional variations. Our study aims to fill this gap.

## Methods

We collected n=500 samples from 10 regions. Data were analyzed using ANOVA. The experiment was conducted under controlled conditions.

## Results

The results indicated that yields decreased by 15% (p<0.05). Furthermore, regional variations were significant. As shown in Figure 1, the pattern was consistent.

## Discussion

These findings suggest that climate change has substantial impacts on agriculture. This is consistent with previous studies (Jones et al., 2019). However, our study has limitations. Future research should examine more regions.
"""

    file_path = tmp_path / "sample.md"
    file_path.write_text(content)
    return str(file_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
