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
        
    def read_docx(self, file_content: bytes) -> Document:
        """Чтение DOCX файла из байтового содержимого"""
        return Document(io.BytesIO(file_content))
    
    def extract_sections(self, doc: Document) -> Dict[str, List[str]]:
        """
        Извлечение разделов документа по заголовкам
        
        Возвращает словарь {заголовок: [абзацы]}
        """
        sections = {}
        current_section = "Введение"  # Начальный раздел по умолчанию
        sections[current_section] = []
        
        for para in doc.paragraphs:
            # Проверяем, является ли параграф заголовком
            if para.style.name.startswith('Heading') or self._is_likely_heading(para):
                current_section = para.text.strip()
                if current_section and current_section not in sections:
                    sections[current_section] = []
            elif para.text.strip():  # Непустые абзацы добавляем в текущий раздел
                sections[current_section].append(para.text.strip())
        
        return sections
    
    def _is_likely_heading(self, para: Paragraph) -> bool:
        """Эвристический метод определения заголовка"""
        text = para.text.strip()
        
        # Короткий текст с точкой в конце обычно не заголовок
        if len(text) < 50 and not text.endswith('.'):
            # Проверка на наличие числа в начале (например, "1. Введение")
            if re.match(r'^\d+\.?\s+\w+', text):
                return True
            # Проверка на все слова с заглавной буквы
            words = text.split()
            if words and all(w[0].isupper() for w in words if w.isalpha()):
                return True
        
        return False
    
    def _combine_paragraphs(self, paragraphs: List[str]) -> str:
        """Объединение абзацев в один текст"""
        return " ".join(paragraphs)
    
    def summarize_long_sections(self, sections: Dict[str, List[str]], max_chars: int = 1000) -> Dict[str, str]:
        """
        Суммаризирует слишком длинные разделы
        
        Возвращает словарь {заголовок: содержание}
        """
        result = {}
        
        for section, paragraphs in sections.items():
            full_text = self._combine_paragraphs(paragraphs)
            
            if len(full_text) > max_chars:
                # Применяем суммаризацию к длинным разделам
                summary = self.summarizer.summarize(full_text)
                result[section] = summary
            else:
                result[section] = full_text
        
        return result
    
    def map_sections_to_poster(self, 
                               sections: Dict[str, str], 
                               mapping: Dict[str, List[str]]) -> Dict[str, str]:
        """
        Отображает разделы документа на поля постера
        
        mapping: словарь {поле_постера: [список_возможных_заголовков]}
        """
        result = {}
        
        for poster_field, possible_headings in mapping.items():
            for heading in possible_headings:
                if heading in sections:
                    result[poster_field] = sections[heading]
                    break
        
        return result
    
    def convert_to_excel(self, poster_data: Dict[str, str]) -> bytes:
        """Преобразование данных постера в Excel файл"""
        df = pd.DataFrame([poster_data])
        output = io.BytesIO()
        df.to_excel(output, index=False)
        output.seek(0)
        return output.getvalue()
    
    def process_docx(self, 
                    file_content: bytes, 
                    section_mapping: Dict[str, List[str]],
                    max_chars: int = 1000) -> Dict[str, Any]:
        """
        Обработка DOCX файла и извлечение данных для постера
        
        section_mapping: словарь {поле_постера: [список_возможных_заголовков]}
        """
        doc = self.read_docx(file_content)
        sections = self.extract_sections(doc)
        summarized_sections = self.summarize_long_sections(sections, max_chars)
        poster_data = self.map_sections_to_poster(summarized_sections, section_mapping)
        
        return poster_data
