import pandas as pd
from typing import Dict, List, Any, Optional
import io


class ExcelProcessor:
    @staticmethod
    def read_excel(file_content: bytes, sheet_name: Optional[str] = None) -> pd.DataFrame:
        """Чтение Excel файла из байтового содержимого"""
        return pd.read_excel(io.BytesIO(file_content), sheet_name=sheet_name)
    
    @staticmethod
    def read_csv(file_content: bytes, delimiter: str = ',', encoding: str = 'utf-8') -> pd.DataFrame:
        """Чтение CSV файла из байтового содержимого"""
        return pd.read_csv(io.BytesIO(file_content), delimiter=delimiter, encoding=encoding)
    
    @staticmethod
    def extract_poster_data(df: pd.DataFrame, mapping: Dict[str, str]) -> Dict[str, Any]:
        """
        Извлечение данных для постера на основе маппинга колонок
        
        mapping: словарь {поле_постера: имя_колонки_в_таблице}
        """
        result = {}
        for poster_field, column_name in mapping.items():
            if column_name in df.columns:
                # Для текстовых полей берем первое ненулевое значение
                values = df[column_name].dropna()
                if not values.empty:
                    result[poster_field] = str(values.iloc[0])
        
        return result
    
    @staticmethod
    def process_file(
        file_content: bytes, 
        file_type: str, 
        mapping: Dict[str, str],
        **kwargs
    ) -> Dict[str, Any]:
        """
        Обработка файла и извлечение данных для постера
        
        file_type: 'excel' или 'csv'
        """
        if file_type == 'excel':
            df = ExcelProcessor.read_excel(file_content, **kwargs)
        elif file_type == 'csv':
            df = ExcelProcessor.read_csv(file_content, **kwargs)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")
        
        return ExcelProcessor.extract_poster_data(df, mapping)
