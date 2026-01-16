# Paper Writer - 论文写作辅助系统

from .config import Config, get_config
from .analyzer.journal_style_analyzer import JournalStyleAnalyzer, analyze_journal_style
from .literature.db_manager import LiteratureDatabaseManager, create_literature_database
# from .coordinator.multi_agent_coordinator import MultiAgentCoordinator, run_coordinator  # 暂时注释掉
# from .integrator.draft_integrator import DraftIntegrator, integrate_sections  # 暂时注释掉

__version__ = "0.1.0"

__all__ = [
    "Config",
    "get_config",
    "JournalStyleAnalyzer",
    "analyze_journal_style",
    "LiteratureDatabaseManager",
    "create_literature_database",
    # "MultiAgentCoordinator",  # 暂时注释掉
    # "run_coordinator",  # 暂时注释掉
    # "DraftIntegrator",  # 暂时注释掉
    # "integrate_sections",  # 暂时注释掉
]
