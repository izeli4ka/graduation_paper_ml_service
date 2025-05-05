from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Dict, Optional
import json
from app.processors.excel_processor import ExcelProcessor
from app.processors.docx_processor import DocxProcessor
from app.processors.summary import BartSummarizer


router = APIRouter()


# Инициализация обработчиков
excel_processor = ExcelProcessor()
summarizer = BartSummarizer()
docx_processor = DocxProcessor(summarizer)


@router.post("/process/excel")
async def process_excel_file(
    file: UploadFile = File(...),
    mapping: str = Form(...),  # JSON строка с маппингом полей
    sheet_name: Optional[str] = Form(None),
    delimiter: str = Form(","),
    encoding: str = Form("utf-8")
):
    """Обработка Excel/CSV файла"""
    try:
        # Проверка формата файла
        file_content = await file.read()
        file_extension = file.filename.split(".")[-1].lower()
        
        # Преобразование JSON маппинга в словарь
        field_mapping = json.loads(mapping)
        
        if file_extension in ["xlsx", "xls"]:
            poster_data = excel_processor.process_file(
                file_content, 
                "excel", 
                field_mapping,
                sheet_name=sheet_name
            )
        elif file_extension == "csv":
            poster_data = excel_processor.process_file(
                file_content, 
                "csv", 
                field_mapping,
                delimiter=delimiter,
                encoding=encoding
            )
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported file format: {file_extension}")
        
        return {"poster_data": poster_data}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/process/docx")
async def process_docx_file(
    file: UploadFile = File(...),
    section_mapping: str = Form(...),  # JSON строка с маппингом разделов
    max_chars: int = Form(1000)
):
    """Обработка DOCX файла"""
    try:
        # Проверка формата файла
        if not file.filename.endswith(".docx"):
            raise HTTPException(status_code=400, detail="Only .docx files are supported")
        
        file_content = await file.read()
        
        # Преобразование JSON маппинга в словарь
        mapping = json.loads(section_mapping)
        
        # Обработка DOCX файла
        poster_data = docx_processor.process_docx(
            file_content, 
            mapping,
            max_chars=max_chars
        )
        
        # Конвертация данных в Excel
        excel_bytes = docx_processor.convert_to_excel(poster_data)
        
        # Обрабатываем Excel как обычно
        return {
            "poster_data": poster_data,
            "excel_data": {
                "content": excel_bytes,
                "filename": file.filename.replace(".docx", ".xlsx")
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
