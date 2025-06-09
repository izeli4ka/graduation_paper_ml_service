from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Dict, List, Optional, Any
from pathlib import Path
import base64
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
    file: Optional[UploadFile] = File(None),
    file_path: Optional[str] = Form(None),         
    mapping: Optional[str] = Form(None),           
    language: Optional[str] = Form(None),          
    template: Optional[UploadFile] = File(None),   
    template_sheet_name: Optional[str] = Form(None),
    sheet_name: Optional[str] = Form(None),
    delimiter: str = Form(","),
    encoding: str = Form("utf-8")
):
    """
    Обработка Excel/CSV файла с поддержкой:
     - загрузки через upload (file) или пути на сервере (file_path)
     - явного маппинга (mapping)
     - языковых шаблонов (language)
     - файла-шаблона (template)
    """
    try:
        # Загружаем содержимое
        if file_path:
            try:
                with open(file_path, "rb") as f:
                    file_content = f.read()
                file_name = file_path.split("/")[-1]
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Cannot read file at path: {e}")
        elif file:
            file_content = await file.read()
            file_name = file.filename
        else:
            raise HTTPException(status_code=400, detail="Either 'file' or 'file_path' must be provided")

        file_ext = file_name.split('.')[-1].lower()

        # Подготавливаем mаппинг
        mapping_dict: Optional[Dict[str, str]] = None
        if mapping:
            mapping_dict = json.loads(mapping)

        template_content: Optional[bytes] = None
        if template:
            template_content = await template.read()

        # Выбираем стратегию обработки
        if file_ext in ["xlsx", "xls"]:
            poster_data = excel_processor.process_file(
                file_content=file_content,
                file_type='excel',
                mapping=mapping_dict,
                language=language,
                template_content=template_content,
                template_sheet_name=template_sheet_name,
                sheet_name=sheet_name,
                delimiter=delimiter,
                encoding=encoding
            )
        elif file_ext == "csv":
            poster_data = excel_processor.process_file(
                file_content=file_content,
                file_type='csv',
                mapping=mapping_dict,
                language=language,
                template_content=None,
                sheet_name=None,
                delimiter=delimiter,
                encoding=encoding
            )
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported file format: {file_ext}")

        return {"poster_data": poster_data}

    except ValueError as ve:
        # Ошибки валидации маппинга/языка
        raise HTTPException(status_code=400, detail=str(ve))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))





@router.post("/process/docx")
async def process_docx_file(
    file: Optional[UploadFile]    = File(None),
    file_path: Optional[str]      = Form(None),
    max_chars:    int             = Form(1000),
    summarize:    bool            = Form(True)  # <-- новый параметр
) -> Dict[str, Any]:
    """
    Обработка DOCX:
      - file или file_path
      - max_chars: порог для суммаризации
      - summarize: включить/выключить суммаризацию
    """
    # 1) Загрузка байтов
    if file_path:
        p = Path(file_path)
        if not p.exists():
            raise HTTPException(400, f"File not found: {file_path}")
        content = p.read_bytes()
        fname   = p.name
    elif file:
        content = await file.read()
        fname   = file.filename
    else:
        raise HTTPException(400, "Provide either 'file' or 'file_path'")

    # 2) Проверка расширения
    if not fname.lower().endswith(".docx"):
        raise HTTPException(400, "Only .docx files are supported")

    # 3) Извлечение разделов
    doc      = docx_processor.read_docx(content)
    sections = docx_processor.extract_sections(doc)

    # 4) Либо суммаризуем длинные секции, либо просто собираем текст
    if summarize:
        poster_data = docx_processor.summarize_sections(sections, max_chars)
    else:
        poster_data = { title: " ".join(paras) for title, paras in sections.items() }

    # 5) Конвертация в Excel + Base64
    excel_bytes = docx_processor.convert_to_excel(poster_data)
    excel_name  = Path(fname).with_suffix(".xlsx").name
    excel_b64   = base64.b64encode(excel_bytes).decode("ascii")

    return {
        "poster_data": poster_data,
        "excel_data": {
            "filename":       excel_name,
            "content_base64": excel_b64
        }
    }