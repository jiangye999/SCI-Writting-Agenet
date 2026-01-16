# Document Processor - 文档处理器

from .simple_parser import (
    DocumentProcessor,
    DocumentElement,
    ParsedSection,
    SimpleDocumentParser,
)
from .word_analyzer import (
    WordDocumentAnalyzer,
    DocumentAnalysisResult,
    ImageElement,
    TableElement,
    TextElement,
    CorrectedContent,
    analyze_document_with_review,
)

__version__ = "0.2.0"

__all__ = [
    "DocumentProcessor",
    "DocumentElement",
    "ParsedSection",
    "SimpleDocumentParser",
    "WordDocumentAnalyzer",
    "DocumentAnalysisResult",
    "ImageElement",
    "TableElement",
    "TextElement",
    "CorrectedContent",
    "analyze_document_with_review",
]
