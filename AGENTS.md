# AGENTS.md - Paper Writer Codebase Guide

This document provides guidelines for AI agents working on this codebase.

## Build/Lint/Test Commands

### Testing
```bash
# Run all tests
pytest

# Run a single test file
pytest tests/test_core.py

# Run a specific test class
pytest tests/test_core.py::TestCoordinator

# Run a specific test method
pytest tests/test_core.py::TestCoordinator::test_task_creation

# Run with coverage
pytest --cov=src

# Verbose output with short traceback
pytest -v --tb=short
```

### Linting & Formatting
```bash
# Format code (Black)
black src/ tests/

# Lint code (Flake8)
flake8 src/ tests/

# Type checking (Mypy)
mypy src/

# All checks
black src/ tests/ && flake8 src/ tests/ && mypy src/
```

### Running the Application
```bash
# CLI entry point
python src/main.py <command> [args]

# Web UI
streamlit run app.py

# Direct module execution
python -m src.analyzer <papers_dir> <output_dir> [journal_name]
```

## Code Style Guidelines

### Imports
- Use absolute imports for external packages: `import pandas as pd`
- Use relative imports for internal modules: `from ..config import Config`
- Group imports in this order:
  1. Standard library
  2. Third-party packages
  3. Local application imports
- Example:
```python
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional

import click
from rich import print as rprint

from src.config import Config
from src.analyzer import JournalStyleAnalyzer
```

### Type Hints
- Use type hints for all function parameters and return values
- Prefer simple types over complex generics when clear
- Use `Optional[T]` instead of `Union[T, None]`
- Example:
```python
def analyze_journal_style(
    papers_dir: str,
    output_dir: str,
    journal_name: str = "Target Journal"
) -> Dict[str, str]:
```

### Docstrings
- Use triple quotes for all docstrings
- Document all public classes and functions
- Use simple English, Chinese comments for Chinese-specific terms
- Example:
```python
def analyze_text(self, text: str, section: str = "general") -> Dict:
    """
    Analyze single text section style features

    Args:
        text: The text to analyze
        section: Section name (e.g., "introduction", "methods")

    Returns:
        Style analysis results dictionary
    """
```

### Naming Conventions
- **Classes**: PascalCase (e.g., `JournalStyleAnalyzer`, `MultiAgentCoordinator`)
- **Functions/Variables**: snake_case (e.g., `analyze_journal_style`, `output_dir`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `DEFAULT_TIMEOUT`, `MAX_RETRIES`)
- **Private Methods**: Prefix with underscore (e.g., `_extract_text()`)

### Error Handling
- Use specific exception types when possible
- Always include error context in messages
- Let exceptions propagate for unexpected errors
- Example:
```python
try:
    result = analyze_journal_style(papers_dir, output_dir, journal_name)
except FileNotFoundError as e:
    print(f"Error: Paper directory not found - {e}")
    sys.exit(1)
except Exception as e:
    print(f"Unexpected error: {e}")
    raise
```

### Data Classes
- Use `@dataclass` for simple data containers
- Provide default values with `field(default_factory=dict)` for mutable types
- Example:
```python
from dataclasses import dataclass, field
from typing import Dict, List, Optional

@dataclass
class SectionResult:
    section_name: str
    content: str
    word_count: int
    citations_used: List[str]
    quality_score: float
    status: str
```

### File Organization
- Main entry points: `src/main.py` (CLI), `app.py` (Web UI)
- Core modules in `src/analyzer/`, `src/coordinator/`, `src/integrator/`
- Tests in `tests/` directory
- Configuration in `config/config.yaml`

### Code Patterns
- Use `Path` from pathlib for file operations
- Always specify encoding for text operations: `Path.read_text(encoding="utf-8")`
- Use context managers (`with` statements) for resource handling
- Example:
```python
from pathlib import Path

config_path = Path("config/config.yaml")
with open(config_path, "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)
```

### Module Structure
- Each module should have:
  1. Module docstring at top
  2. Imports
  3. Constants
  4. Classes
  5. Functions
  6. `if __name__ == "__main__":` block (optional)

### String Formatting
- Use f-strings for simple interpolation
- Use `.format()` for complex cases
- Example:
```python
# F-string
st.write(f"已上传 {file_count} 个文件")

# Format with named parameters
"文件路径: {path}".format(path=output_path)
```

### CLI Commands (using Click)
- Use `@click.group()` for command groups
- Use `@click.command()` for individual commands
- Add help text with `help="description"`
- Example:
```python
@click.command()
@click.argument("papers_dir", type=click.Path(exists=True))
@click.option("--journal", "-j", default="Target Journal")
def analyze(papers_dir: str, journal: str):
    """Analyze target journal writing style"""
```

### Web UI (Streamlit)
- Use `st.set_page_config()` for page settings
- Use `st.columns()` for layouts
- Use `st.session_state` for persistent state
- Use `st.spinner()` for long operations

### Quality Thresholds
- Completeness: 0.80
- Style match: 0.75
- Citation accuracy: 0.95
- Overall: 0.85

### Key Dependencies
- anthropic-sdk, openai (AI providers)
- streamlit (Web UI)
- spacy, nltk (NLP processing)
- pdfplumber, python-docx (Document parsing)
- click, rich (CLI tools)
- pytest (Testing)
