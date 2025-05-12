import pandas as pd
import math
import io
from typing import Dict, Any, Optional


class ExcelProcessor:
    # Предустановленные шаблоны маппинга для разных языков
    LANGUAGE_TEMPLATES: Dict[str, Dict[str, str]] = {
        'ru': {
            'Название проекта': 'Название проекта',
            'Титульная информация': 'Титульная информация',
            'Краткое описание': 'Краткое описание',
            'Ключевые слова': 'Ключевые слова',
            'Актуальность': 'Актуальность',
            'Цель работы': 'Цель работы',
            'Подробное описание': 'Подробное описание',
            'Результаты': 'Результаты'
        },
        'en': {
            'Project Title': 'Project Title',
            'Title Information': 'Title Information',
            'Short Description': 'Short Description',
            'Keywords': 'Keywords',
            'Relevance': 'Relevance',
            'Objective': 'Objective',
            'Detailed Description': 'Detailed Description',
            'Results': 'Results'
        },
        'de': {
            'Projektname': 'Projektname',
            'Titelinformationen': 'Titelinformationen',
            'Kurze Beschreibung': 'Kurze Beschreibung',
            'Schlüsselwörter': 'Schlüsselwörter',
            'Relevanz': 'Relevanz',
            'Ziel der Arbeit': 'Ziel der Arbeit',
            'Detaillierte описание': 'Detaillierte Beschreibung',
            'Ergebnisse': 'Ergebnisse'
        }
    }

    @classmethod
    def get_template_mapping(cls, language: str) -> Dict[str, str]:
        return cls.LANGUAGE_TEMPLATES.get(language, {})

    @staticmethod
    def read_excel(file_content: bytes, sheet_name: Optional[str] = None) -> pd.DataFrame:
        """
        Читает Excel из байтов.
        Если sheet_name указан — читает указанный лист.
        Если sheet_name=None — читает первый лист.
        В любом случае возвращает DataFrame (а не dict).
        """
        buf = io.BytesIO(file_content)
        try:
            # если sheet_name указан и непустой, передаём его, иначе вызываем без sheet_name
            if sheet_name:
                df = pd.read_excel(buf, sheet_name=sheet_name)
            else:
                df = pd.read_excel(buf)  # по умолчанию первый лист
        except Exception as e:
            raise ValueError(f"Error reading Excel file: {e}")

        # pd.read_excel с sheet_name=None возвращает dict[str,DataFrame]
        if isinstance(df, dict):
            if not df:
                raise ValueError("Excel file contains no sheets")
            # берём первый DataFrame
            df = next(iter(df.values()))

        return df

    @staticmethod
    def read_csv(file_content: bytes, delimiter: str = ',', encoding: str = 'utf-8') -> pd.DataFrame:
        """
        Читает CSV из байтов, возвращает DataFrame.
        """
        buf = io.BytesIO(file_content)
        try:
            return pd.read_csv(buf, delimiter=delimiter, encoding=encoding)
        except Exception as e:
            raise ValueError(f"Error reading CSV file: {e}")

    @staticmethod
    def extract_poster_data(df: pd.DataFrame, mapping: Dict[str, str]) -> Dict[str, Any]:
        """
        Извлечение данных для постера на основе маппинга {поле: колонка}.
        Берёт первое ненулевое значение в каждой колонке.
        """
        result: Dict[str, Any] = {}
        for poster_field, column_name in mapping.items():
            if column_name in df.columns:
                values = df[column_name].dropna()
                if not values.empty:
                    result[poster_field] = str(values.iloc[0])
        return result

    @staticmethod
    def sanitize_value(val: Any) -> Any:
        """
        Заменяет NaN/inf на None, рекурсивно обрабатывает списки и словари.
        """
        if isinstance(val, float):
            if math.isnan(val) or math.isinf(val):
                return None
        elif isinstance(val, list):
            return [ExcelProcessor.sanitize_value(x) for x in val]
        elif isinstance(val, dict):
            return {k: ExcelProcessor.sanitize_value(v) for k, v in val.items()}
        return val

    @classmethod
    def sanitize_data(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Применяет sanitize_value ко всем значениям словаря.
        """
        return {k: cls.sanitize_value(v) for k, v in data.items()}

    def process_file(
        self,
        file_content: bytes,
        file_type: str,
        mapping: Optional[Dict[str, str]] = None,
        language: Optional[str] = None,
        template_content: Optional[bytes] = None,
        template_sheet_name: Optional[str] = None,
        sheet_name: Optional[str] = None,
        delimiter: str = ',',
        encoding: str = 'utf-8'
    ) -> Dict[str, Any]:
        """
        1) Выбирает mapping: файл-шаблон > явный mapping > языковой шаблон
        2) Читает DataFrame (Excel или CSV)
        3) Извлекает данные по mapping
        4) Санитизирует результат
        """
        # 1) Построение mapping
        if template_content:
            # mapping = заголовок→заголовок из шаблонного файла
            tmpl_df = self.read_excel(template_content, sheet_name=template_sheet_name)
            mapping = {col: col for col in tmpl_df.columns}
        elif mapping is None and language:
            mapping = self.get_template_mapping(language)

        if not mapping:
            raise ValueError("mapping must be provided, or language/template_content must be set")

        # 2) Чтение 
        if file_type == 'excel':
            df = self.read_excel(file_content, sheet_name=sheet_name)
        elif file_type == 'csv':
            df = self.read_csv(file_content, delimiter=delimiter, encoding=encoding)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")

        # 3) Извлечение
        data = self.extract_poster_data(df, mapping)

        # 4) Санитизация
        return self.sanitize_data(data)
