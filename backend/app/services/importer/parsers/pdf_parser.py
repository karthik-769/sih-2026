import io
import re
import logging
from typing import List, Dict, Any, Optional
import fitz  # PyMuPDF
from app.services.importer.parsers.column_mapper import ColumnMapper
from app.core.config import settings

logger = logging.getLogger(__name__)


class PdfParser:
    """
    Extracts structured and semi-structured safety incident reports from PDF files.
    Identifies multiple reports per document using regex delimiters, header keys, and section markers.
    Includes OCR fallback for scanned images when selectable text layer is absent.
    """

    REPORT_SPLIT_PATTERNS = [
        r'(?i)(?:^|\n)(?:[-=_]{3,}|\*{3,})\s*(?:\n|$)',                  # Divider lines like --- or ===
        r'(?i)(?:^|\n)(?:Report\s+\d+|Incident\s+\d+|Case\s+\d+)[:\s-]*', # Report 1, Report 2
        r'(?i)(?:^|\n)(?=Case\s*ID\s*:)',                                 # Case ID:
        r'(?i)(?:^|\n)(?=Report\s*ID\s*:)',                               # Report ID:
    ]

    FIELD_EXTRACTION_PATTERNS = {
        "case_id": r'(?i)(?:Case\s*ID|Report\s*ID|Incident\s*ID|ID)\s*[:=-]\s*([^\n\r]+)',
        "job_role": r'(?i)(?:Job\s*Role|Role|Worker\s*Role|Designation|Reporter)\s*[:=-]\s*([^\n\r]+)',
        "department": r'(?i)(?:Department|Dept)\s*[:=-]\s*([^\n\r]+)',
        "location": r'(?i)(?:Location|Plant\s*Location|Unit|Site|Area)\s*[:=-]\s*([^\n\r]+)',
        "task": r'(?i)(?:Task|Activity|Work\s*Task)\s*[:=-]\s*([^\n\r]+)',
        "incident_type": r'(?i)(?:Incident\s*Type|Type|Category|Classification)\s*[:=-]\s*([^\n\r]+)',
        "date_time": r'(?i)(?:Date(?:/Time)?|Reported\s*Date|DateTime|Timestamp)\s*[:=-]\s*([^\n\r]+)',
        "description": r'(?i)(?:Description|Details|Narrative|Observation|Findings|Event)\s*[:=-]\s*([\s\S]+?)(?=(?:Case\s*ID|Report\s*\d+|Department|Location|Task|Incident\s*Type|Date|$))',
    }

    @classmethod
    def parse_pdf_bytes(cls, file_bytes: bytes, filename: str = "upload.pdf") -> List[Dict[str, Any]]:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        extracted_reports: List[Dict[str, Any]] = []

        all_page_texts: List[Tuple[int, str]] = []

        for page_num, page in enumerate(doc, start=1):
            text = page.get_text("text").strip()
            
            # If text is empty or very short, check OCR
            if len(text) < 20 and settings.ENABLE_OCR:
                ocr_text = cls._perform_ocr_on_page(page)
                if ocr_text:
                    text = ocr_text

            if text:
                all_page_texts.append((page_num, text))

        if not all_page_texts:
            return []

        # Parse reports across pages
        row_counter = 0
        for page_num, page_text in all_page_texts:
            reports_in_page = cls._segment_and_parse_reports(page_text, page_num)
            for rep in reports_in_page:
                row_counter += 1
                rep["source_row"] = row_counter
                extracted_reports.append(rep)

        return extracted_reports

    @classmethod
    def _segment_and_parse_reports(cls, page_text: str, page_num: int) -> List[Dict[str, Any]]:
        """
        Segments a page's text into one or more distinct incident report blocks.
        """
        # Try finding explicit boundaries
        blocks = [page_text]
        
        # Check if multiple Case IDs exist in page_text
        case_id_matches = list(re.finditer(r'(?i)(?:Case\s*ID|Report\s*ID|Incident\s*ID)\s*[:=-]', page_text))
        if len(case_id_matches) > 1:
            # Split by Case ID positions
            indices = [m.start() for m in case_id_matches]
            indices.append(len(page_text))
            blocks = []
            for i in range(len(indices) - 1):
                block_chunk = page_text[indices[i]:indices[i+1]].strip()
                if block_chunk:
                    blocks.append(block_chunk)
        else:
            # Check divider pattern
            split_by_divider = re.split(r'(?i)(?:^|\n)(?:[-=_]{3,}|\*{3,})\s*(?:\n|$)', page_text)
            if len(split_by_divider) > 1:
                blocks = [b.strip() for b in split_by_divider if len(b.strip()) > 10]

        reports: List[Dict[str, Any]] = []

        for block in blocks:
            parsed = cls._parse_single_block(block, page_num)
            if parsed and parsed.get("description"):
                reports.append(parsed)

        return reports

    @classmethod
    def _parse_single_block(cls, block_text: str, page_num: int) -> Optional[Dict[str, Any]]:
        if not block_text or len(block_text.strip()) < 10:
            return None

        record: Dict[str, Any] = {
            "source_row": None,
            "source_page": page_num,
            "case_id": None,
            "job_role": None,
            "department": None,
            "location": None,
            "task": None,
            "incident_type": None,
            "date_time": None,
            "description": "",
        }

        # Extract structured key-value fields
        for field, pattern in cls.FIELD_EXTRACTION_PATTERNS.items():
            if field == "description":
                continue
            m = re.search(pattern, block_text)
            if m:
                val = m.group(1).strip()
                # Clean trailing field markers if any
                val = re.split(r'(?i)\s+(?:Job\s*Role|Department|Location|Task|Incident|Date|Description):', val)[0].strip()
                if field == "incident_type":
                    record["incident_type"] = ColumnMapper.normalize_incident_type(val)
                else:
                    record[field] = val

        # Extract Description
        desc_match = re.search(cls.FIELD_EXTRACTION_PATTERNS["description"], block_text)
        if desc_match:
            desc_val = desc_match.group(1).strip()
            record["description"] = desc_val
        else:
            # If no explicit "Description:" tag, extract remaining lines that don't match standard key: value headers
            lines = block_text.split('\n')
            desc_lines = []
            for line in lines:
                l_strip = line.strip()
                if not l_strip:
                    continue
                if any(re.match(r'(?i)^(?:Case\s*ID|Job\s*Role|Department|Location|Task|Incident\s*Type|Date(?:/Time)?|Report\s*\d+)\s*[:=-]', l_strip) for _ in [1]):
                    continue
                desc_lines.append(l_strip)
            if desc_lines:
                record["description"] = " ".join(desc_lines)
            else:
                record["description"] = block_text.strip()

        return record

    @classmethod
    def _perform_ocr_on_page(cls, page: fitz.Page) -> Optional[str]:
        """Performs pytesseract OCR on page pixmap image if Tesseract is available."""
        try:
            import pytesseract
            from PIL import Image

            pix = page.get_pixmap(dpi=200)
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            text = pytesseract.image_to_string(img)
            return text.strip()
        except Exception as e:
            logger.warning(f"OCR execution skipped or unavailable: {e}")
            return None
