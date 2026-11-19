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
        elif ext == ".zip":
            return DocumentParser._parse_project_zip(file_content)
        elif ext in [".txt", ".md", ".json"]:
            return DocumentParser._parse_text(file_content)
        else:
            raise ValidationError(f"Unsupported file format: {ext}. Supported: PDF, DOCX, XLSX, CSV, ZIP, TXT, MD.")

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

    @staticmethod
    def _parse_project_zip(content: bytes, destination_dir: Any = None) -> str:
        import zipfile
        try:
            with zipfile.ZipFile(io.BytesIO(content)) as zf:
                file_list = zf.namelist()
                # Security: prevent zip slip path traversal
                for member in file_list:
                    if member.startswith("/") or ".." in member:
                        raise ValidationError("Security Error: Insecure ZIP archive containing relative path traversal.")

                if destination_dir:
                    dest = Path(destination_dir)
                    dest.mkdir(parents=True, exist_ok=True)
                    zf.extractall(dest)

                summary_lines = [f"=== Client Project Archive Analysis ({len(file_list)} files) ==="]

                readme_files = [f for f in file_list if "readme" in f.lower() and not f.endswith("/")]
                if readme_files:
                    readme_content = zf.read(readme_files[0]).decode("utf-8", errors="replace")
                    summary_lines.append(f"\n--- Readme Overview ({readme_files[0]}) ---\n{readme_content[:1500]}")

                # Identify source code files
                code_files = [
                    f for f in file_list
                    if f.endswith((".py", ".js", ".ts", ".jsx", ".tsx", ".html"))
                    and not any(x in f for x in ["node_modules", ".venv", "__pycache__", "dist", "build"])
                ]

                summary_lines.append(f"\nDetected Source Code Files ({len(code_files)} files):")
                for cf in code_files[:15]:
                    summary_lines.append(f"  - {cf}")

                # Extract UI elements (forms, inputs, buttons, test-ids)
                ui_files = [f for f in code_files if f.endswith((".html", ".jsx", ".tsx", ".vue"))]
                ui_elements_found = []
                for uf in ui_files[:6]:
                    try:
                        u_text = zf.read(uf).decode("utf-8", errors="replace")
                        for line in u_text.splitlines():
                            line_s = line.strip()
                            if any(k in line_s.lower() for k in ["<form", "<input", "<button", "id=", "name=", "data-testid="]):
                                if len(line_s) < 140:
                                    ui_elements_found.append(f"[{uf}] {line_s}")
                    except Exception:
                        pass

                if ui_elements_found:
                    summary_lines.append("\nDetected Client UI Form & Action Locators:")
                    for el in ui_elements_found[:20]:
                        summary_lines.append(f"  {el}")

                return "\n".join(summary_lines)
        except Exception as e:
            logger.error(f"Error parsing ZIP archive: {e}")
            raise ValidationError(f"Failed to process project ZIP archive: {e}")
