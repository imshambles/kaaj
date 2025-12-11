"""
PDF Parser Service - Extract text from lender guideline PDFs
"""
import io
from typing import Optional
import pdfplumber


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """
    Extract all text content from a PDF file.
    
    Args:
        pdf_bytes: Raw PDF file bytes
        
    Returns:
        Extracted text as a single string
    """
    text_parts = []
    
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
    
    return "\n\n".join(text_parts)


def extract_tables_from_pdf(pdf_bytes: bytes) -> list[list[list[str]]]:
    """
    Extract tables from a PDF file.
    
    Args:
        pdf_bytes: Raw PDF file bytes
        
    Returns:
        List of tables, where each table is a list of rows
    """
    tables = []
    
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            page_tables = page.extract_tables()
            if page_tables:
                tables.extend(page_tables)
    
    return tables


def parse_pdf(pdf_bytes: bytes) -> dict:
    """
    Parse a PDF and return structured content.
    
    Args:
        pdf_bytes: Raw PDF file bytes
        
    Returns:
        Dict with text content and metadata
    """
    text = extract_text_from_pdf(pdf_bytes)
    tables = extract_tables_from_pdf(pdf_bytes)
    
    # Get page count
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        page_count = len(pdf.pages)
    
    return {
        "text": text,
        "tables": tables,
        "page_count": page_count,
        "char_count": len(text),
    }
