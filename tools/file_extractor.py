"""File text extraction — PDF, DOCX, images with OCR."""

from __future__ import annotations

import io
import logging
from pathlib import Path
from typing import BinaryIO

# Configure logging
log = logging.getLogger("privasend.file_extractor")

# Supported file types
SUPPORTED_TYPES = {
    "application/pdf": "pdf",
    "text/plain": "txt",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
    "image/png": "png",
    "image/jpeg": "jpg",
    "image/jpg": "jpg",
    "image/tiff": "tiff",
}

UNSUPPORTED_TYPES = set(SUPPORTED_TYPES.keys())


class ExtractionError(Exception):
    """Raised when file extraction fails."""
    pass


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract text from PDF using pdfplumber."""
    try:
        import pdfplumber
    except ImportError:
        log.error("pdfplumber not installed")
        raise ExtractionError("PDF support not available. Install pdfplumber.")
    
    text_parts = []
    try:
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for i, page in enumerate(pdf.pages):
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(f"--- Page {i+1} ---\n{page_text}")
    except Exception as e:
        log.error(f"PDF extraction failed: {e}")
        raise ExtractionError(f"Could not read PDF: {e}")
    
    return "\n\n".join(text_parts) if text_parts else ""


def extract_text_from_docx(file_bytes: bytes) -> str:
    """Extract text from DOCX using python-docx."""
    try:
        import docx
    except ImportError:
        log.error("python-docx not installed")
        raise ExtractionError("DOCX support not available. Install python-docx.")
    
    try:
        doc = docx.Document(io.BytesIO(file_bytes))
        text_parts = []
        for para in doc.paragraphs:
            if para.text.strip():
                text_parts.append(para.text)
        return "\n".join(text_parts)
    except Exception as e:
        log.error(f"DOCX extraction failed: {e}")
        raise ExtractionError(f"Could not read DOCX: {e}")


def extract_text_from_txt(file_bytes: bytes) -> str:
    """Extract text from plain text file."""
    try:
        # Try UTF-8 first
        return file_bytes.decode("utf-8")
    except UnicodeDecodeError:
        try:
            # Fallback to latin-1
            return file_bytes.decode("latin-1")
        except Exception as e:
            log.error(f"Text decoding failed: {e}")
            raise ExtractionError(f"Could not decode text file: {e}")


def extract_text_from_image(file_bytes: bytes) -> str:
    """Extract text from image using pytesseract OCR."""
    try:
        from PIL import Image
        import pytesseract
    except ImportError:
        log.error("pytesseract or PIL not installed")
        raise ExtractionError("OCR not available. Install pytesseract and Pillow.")
    
    try:
        image = Image.open(io.BytesIO(file_bytes))
        # Convert to RGB if necessary (for PNG with transparency)
        if image.mode in ("RGBA", "P"):
            image = image.convert("RGB")
        
        text = pytesseract.image_to_string(image, lang="eng")
        return text.strip()
    except Exception as e:
        log.error(f"OCR failed: {e}")
        raise ExtractionError(f"Could not extract text from image: {e}")


def extract_text_from_file(file_bytes: bytes, content_type: str) -> str:
    """
    Extract text from a file based on its content type.
    
    Args:
        file_bytes: Raw file content
        content_type: MIME type (e.g., 'application/pdf')
    
    Returns:
        Extracted text
    
    Raises:
        ExtractionError: If extraction fails
        ValueError: If content type not supported
    """
    if content_type not in SUPPORTED_TYPES:
        raise ValueError(f"Unsupported file type: {content_type}")
    
    file_type = SUPPORTED_TYPES[content_type]
    log.info(f"Extracting text from {file_type} file ({len(file_bytes)} bytes)")
    
    if file_type == "pdf":
        return extract_text_from_pdf(file_bytes)
    elif file_type == "docx":
        return extract_text_from_docx(file_bytes)
    elif file_type == "txt":
        return extract_text_from_txt(file_bytes)
    elif file_type in ("png", "jpg", "tiff"):
        return extract_text_from_image(file_bytes)
    else:
        raise ValueError(f"Unknown file type: {file_type}")


def get_file_extension(content_type: str) -> str:
    """Get file extension for content type."""
    return SUPPORTED_TYPES.get(content_type, "bin")
