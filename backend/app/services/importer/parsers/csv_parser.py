import csv
import io
from typing import List, Dict, Any, Optional
from app.services.importer.parsers.column_mapper import ColumnMapper


class CsvParser:
    """
    Parses CSV files into normalized safety report dictionaries.
    Supports UTF-8, UTF-8-SIG (BOM), Latin-1, whitespace stripping, and dialect sniffing.
    """

    SUPPORTED_ENCODINGS = ["utf-8-sig", "utf-8", "latin-1", "cp1252"]

    @classmethod
    def parse_csv_bytes(cls, file_bytes: bytes, filename: str = "upload.csv") -> List[Dict[str, Any]]:
        # 1. Decode text
        decoded_text = None
        for enc in cls.SUPPORTED_ENCODINGS:
            try:
                decoded_text = file_bytes.decode(enc)
                break
            except (UnicodeDecodeError, LookupError):
                continue

        if decoded_text is None:
            decoded_text = file_bytes.decode("utf-8", errors="replace")

        # 2. Sniff delimiter
        sample = decoded_text[:2048]
        delimiter = ","
        try:
            sniffer = csv.Sniffer()
            dialect = sniffer.sniff(sample, delimiters=",;\t|")
            delimiter = dialect.delimiter
        except Exception:
            # Fallback detection
            if sample.count(";") > sample.count(","):
                delimiter = ";"
            elif sample.count("\t") > sample.count(","):
                delimiter = "\t"

        # 3. Read CSV
        reader = csv.reader(io.StringIO(decoded_text), delimiter=delimiter)
        raw_headers = None
        for r in reader:
            if any(cell.strip() for cell in r):
                raw_headers = [cell.strip() for cell in r]
                break

        if not raw_headers:
            return []

        col_mapping = ColumnMapper.map_columns(raw_headers)
        extracted_rows: List[Dict[str, Any]] = []
        row_num = 1

        for row_values in reader:
            row_num += 1
            if not any(cell.strip() for cell in row_values):
                continue

            record: Dict[str, Any] = {
                "source_row": row_num,
                "source_page": None,
                "case_id": None,
                "job_role": None,
                "department": None,
                "location": None,
                "task": None,
                "incident_type": None,
                "date_time": None,
                "description": "",
            }

            for col_idx, cell_val in enumerate(row_values):
                if cell_val is None:
                    continue
                clean_val = cell_val.strip()
                field_name = col_mapping.get(col_idx)
                if not field_name:
                    continue

                if field_name == "description":
                    record["description"] = clean_val
                elif field_name == "incident_type":
                    record["incident_type"] = ColumnMapper.normalize_incident_type(clean_val)
                elif field_name == "date_time":
                    record["date_time"] = clean_val
                else:
                    record[field_name] = clean_val

            # Fallback only if no header column mapped to description
            if "description" not in col_mapping.values() and not record["description"]:
                text_cells = [c.strip() for c in row_values if len(c.strip()) > 5]
                if text_cells:
                    record["description"] = max(text_cells, key=len)

            extracted_rows.append(record)

        return extracted_rows
