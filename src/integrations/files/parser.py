"""
Multi-format Requirement Document Parser.
Extracts raw text and requirements from PDF, Word (.docx), Excel (.xlsx), CSV, Markdown, and TXT files.
"""

import io
import csv
from pathlib import Path
from typing import Union, List, Dict, Any
from src.core.exceptions import ValidationError
from src.core.logging import get_logger

logger = get_logger("file_parser")


class DocumentParser:
    @staticmethod
    def parse_file(file_content: bytes, filename: str) -> str:
        """Parses raw bytes of an uploaded file into clean text based on file extension."""
        ext = Path(filename).suffix.lower()

        if ext == ".pdf":
            return DocumentParser._parse_pdf(file_content)
        elif ext in [".docx", ".doc"]:
            return DocumentParser._parse_docx(file_content)
        elif ext in [".xlsx", ".xls"]:
            return DocumentParser._parse_excel(file_content)
        elif ext == ".csv":
            return DocumentParser._parse_csv(file_content)
        elif ext in [".txt", ".md", ".json"]:
            return DocumentParser._parse_text(file_content)
        else:
            raise ValidationError(f"Unsupported file format: {ext}. Supported: PDF, DOCX, XLSX, CSV, TXT, MD.")

    @staticmethod
    def _parse_pdf(content: bytes) -> str:
        try:
            from pypdf import PdfReader
            reader = PdfReader(io.BytesIO(content))
            extracted_pages = []
            for i, page in enumerate(reader.pages):
                text = page.extract_text()
                if text:
                    extracted_pages.append(text.strip())
            return "\n\n".join(extracted_pages)
        except Exception as e:
            logger.error(f"Error parsing PDF: {e}")
            raise ValidationError(f"Failed to extract text from PDF: {e}")

    @staticmethod
    def _parse_docx(content: bytes) -> str:
        try:
            import docx
            doc = docx.Document(io.BytesIO(content))
            full_text = []
            for para in doc.paragraphs:
                if para.text.strip():
                    full_text.append(para.text.strip())
            # Also extract tables
            for table in doc.tables:
                for row in table.rows:
                    row_data = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                    if row_data:
                        full_text.append(" | ".join(row_data))
            return "\n".join(full_text)
        except Exception as e:
            logger.error(f"Error parsing DOCX: {e}")
            raise ValidationError(f"Failed to extract text from Word document: {e}")

    @staticmethod
    def _parse_excel(content: bytes) -> str:
        try:
            import openpyxl
            wb = openpyxl.load_workbook(io.BytesIO(content), data_only=True)
            lines = []
            for sheetname in wb.sheetnames:
                sheet = wb[sheetname]
                lines.append(f"--- Sheet: {sheetname} ---")
                for row in sheet.iter_rows(values_only=True):
                    row_vals = [str(cell).strip() for cell in row if cell is not None and str(cell).strip()]
                    if row_vals:
                        lines.append(" | ".join(row_vals))
            return "\n".join(lines)
        except Exception as e:
            logger.error(f"Error parsing Excel: {e}")
            raise ValidationError(f"Failed to extract text from Excel file: {e}")

    @staticmethod
    def _parse_csv(content: bytes) -> str:
        try:
            text = content.decode("utf-8", errors="replace")
            reader = csv.reader(io.StringIO(text))
            lines = []
            for row in reader:
                clean_row = [col.strip() for col in row if col.strip()]
                if clean_row:
                    lines.append(" | ".join(clean_row))
            return "\n".join(lines)
        except Exception as e:
            logger.error(f"Error parsing CSV: {e}")
            raise ValidationError(f"Failed to parse CSV: {e}")

    @staticmethod
    def _parse_text(content: bytes) -> str:
        try:
            return content.decode("utf-8", errors="replace")
        except Exception as e:
            raise ValidationError(f"Failed to decode text file: {e}")
