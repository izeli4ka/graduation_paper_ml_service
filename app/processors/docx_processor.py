from typing import Dict, List, Any, Optional
import io
import re
from docx import Document
from docx.text.paragraph import Paragraph
from app.processors.summary import BartSummarizer
import pandas as pd


class DocxProcessor:
    def __init__(self, summarizer: Optional[BartSummarizer] = None):
        self.summarizer = summarizer or BartSummarizer()

    @staticmethod
    def _ensure_bytes(content: Any) -> bytes:
        if not isinstance(content, (bytes, bytearray)):
            raise ValueError(f"Expected bytes for DOCX content, got {type(content)}")
        return content  # type: ignore

    def read_docx(self, file_content: bytes) -> Document:
        buf = io.BytesIO(self._ensure_bytes(file_content))
        try:
            return Document(buf)
        except Exception as e:
            raise ValueError(f"Error reading DOCX file: {e}")

    def _is_heading(self, para: Paragraph) -> bool:
        # стиль Heading*
        if para.style.name.startswith("Heading"):
            return True
        # или есть хотя бы одна жирная часть
        for run in para.runs:
            if run.bold:
                return True
        # или короткая строка без точки в конце
        text = para.text.strip()
        if 0 < len(text) < 100 and not text.endswith(".") and text.isupper():
            return True
        return False

    def extract_sections(self, doc: Document) -> Dict[str, List[str]]:
        sections: Dict[str, List[str]] = {}
        current: Optional[str] = None

        for para in doc.paragraphs:
            text = para.text.strip()
            if not text:
                continue

            if self._is_heading(para):
                current = text
                sections[current] = []
            elif current:
                sections[current].append(text)

        if not sections:
            raise ValueError("No headings found in DOCX")
        return sections

    def summarize_sections(
        self,
        sections: Dict[str, List[str]],
        max_chars: int
    ) -> Dict[str, str]:
        summarized: Dict[str, str] = {}
        for title, paras in sections.items():
            full = " ".join(paras)
            if len(full) > max_chars:
                summarized[title] = self.summarizer.summarize(full)
            else:
                summarized[title] = full
        return summarized

    def convert_to_excel(self, data: Dict[str, str]) -> bytes:
        df = pd.DataFrame([data])
        buf = io.BytesIO()
        df.to_excel(buf, index=False)
        buf.seek(0)
        return buf.getvalue()

    def process_docx(
        self,
        file_content: bytes,
        max_chars: int = 1000
    ) -> Dict[str, Any]:
        """
        1) Читает DOCX
        2) Извлекает секции по заголовкам
        3) Суммирует длинные секции
        4) Возвращает dict {заголовок: текст}
        """
        doc = self.read_docx(file_content)
        raw_sections = self.extract_sections(doc)
        poster_data = self.summarize_sections(raw_sections, max_chars)
        return poster_data
