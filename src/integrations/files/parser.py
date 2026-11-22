"""
Multi-format Requirement Document Parser.
Extracts raw text and requirements from PDF, Word (.docx), Excel (.xlsx), CSV, Markdown, and TXT files.
Hardened with file size caps, ZIP bomb mitigation, and ZIP slip path traversal defenses.
"""

import io
import csv
import zipfile
from pathlib import Path
from typing import Union, List, Dict, Any
from src.config.settings import settings
from src.core.exceptions import ValidationError
from src.core.logging import get_logger
from src.core.security.audit_logger import audit_logger

logger = get_logger("file_parser")


class DocumentParser:
    @staticmethod
    def parse_file(file_content: bytes, filename: str) -> str:
        """Parses raw bytes of an uploaded file into clean text based on file extension."""
        # Enforce maximum upload size limit (DoS prevention)
        if len(file_content) > settings.MAX_UPLOAD_SIZE_BYTES:
            max_mb = settings.MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)
            audit_logger.log_event(
                action="FILE_UPLOAD_REJECTED_TOO_LARGE",
                status="REJECTED",
                details={"filename": filename, "size_bytes": len(file_content), "limit_mb": max_mb},
                severity="WARNING",
            )
            raise ValidationError(f"File size ({len(file_content)} bytes) exceeds maximum upload limit of {max_mb}MB.")

        ext = Path(filename).suffix.lower()

        audit_logger.log_event(
            action="FILE_PARSE_ATTEMPT",
            status="PROCESSING",
            details={"filename": filename, "extension": ext, "size_bytes": len(file_content)},
        )

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
        try:
            with zipfile.ZipFile(io.BytesIO(content)) as zf:
                infolist = zf.infolist()

                # 1. ZIP Bomb Defense: File count cap
                if len(infolist) > settings.MAX_ZIP_FILES:
                    raise ValidationError(
                        f"Security Error: ZIP archive contains {len(infolist)} files, exceeding limit ({settings.MAX_ZIP_FILES})."
                    )

                # 2. ZIP Bomb Defense: Decompressed total size check
                total_uncompressed = sum(info.file_size for info in infolist)
                if total_uncompressed > settings.MAX_ZIP_DECOMPRESSED_BYTES:
                    max_dec_mb = settings.MAX_ZIP_DECOMPRESSED_BYTES // (1024 * 1024)
                    raise ValidationError(
                        f"Security Error: Decompressed ZIP size ({total_uncompressed} bytes) exceeds limit of {max_dec_mb}MB."
                    )

                # 3. ZIP Slip Defense: Path traversal check
                dest_res = Path(destination_dir).resolve() if destination_dir else None
                for member in infolist:
                    clean_name = member.filename
                    if clean_name.startswith(("/", "\\")) or ".." in clean_name:
                        raise ValidationError(f"Security Error: ZIP entry contains path traversal: {clean_name}")

                    if dest_res:
                        target = (dest_res / clean_name).resolve()
                        if not str(target).startswith(str(dest_res)):
                            raise ValidationError(f"Security Error: Zip slip path traversal detected: {clean_name}")

                if dest_res:
                    dest_res.mkdir(parents=True, exist_ok=True)
                    zf.extractall(dest_res)

                file_list = zf.namelist()
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
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error parsing ZIP archive: {e}")
            raise ValidationError(f"Failed to process project ZIP archive: {e}")
