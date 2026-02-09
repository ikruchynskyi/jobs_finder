import os
import pypdf
import docx
import logging
from fastapi import UploadFile

logger = logging.getLogger(__name__)

async def extract_text_from_file(file_path: str, file_type: str) -> str:
    """
    Extract text from PDF or DOCX file.
    """
    text = ""
    try:
        if file_type == "application/pdf" or file_path.lower().endswith(".pdf"):
            reader = pypdf.PdfReader(file_path)
            for page in reader.pages:
                text += page.extract_text() + "\n"
        
        elif file_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document" or file_path.lower().endswith(".docx"):
            doc = docx.Document(file_path)
            for para in doc.paragraphs:
                text += para.text + "\n"
        
        return text.strip()
    except Exception as e:
        logger.error(f"Failed to extract text from {file_path}: {e}")
        return ""
