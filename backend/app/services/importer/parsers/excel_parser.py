import io
import datetime
from typing import List, Dict, Any, Optional
import openpyxl
from app.services.importer.parsers.column_mapper import ColumnMapper


class ExcelParser:
    """
    Parses Microsoft Excel (.xlsx) workbooks into normalized safety report dictionaries.
    Ignores blank rows and handles varied cell types (dates, floats, formulas, text).
    """

    @classmethod
    def parse_excel_bytes(cls, file_bytes: bytes, filename: str = "upload.xlsx") -> List[Dict[str, Any]]:
        workbook = openpyxl.load_workbook(filename=io.BytesIO(file_bytes), data_only=True)
        sheet = workbook.active
        if not sheet:
            return []

        rows_iter = sheet.iter_rows(values_only=True)
        raw_headers = None
        for r in rows_iter:
            if any(cell is not None and str(cell).strip() for cell in r):
                raw_headers = [str(cell).strip() if cell is not None else "" for cell in r]
                break

        if not raw_headers:
            return []

        col_mapping = ColumnMapper.map_columns(raw_headers)
        if "description" not in col_mapping.values():
            # If header row had no 'description', check if first column or any column contains narrative
            pass

        extracted_rows: List[Dict[str, Any]] = []
        row_num = 1  # 1-indexed (header was row 1)

        for row_values in rows_iter:
            row_num += 1
            if not any(cell is not None and str(cell).strip() for cell in row_values):
                continue  # Skip completely empty rows

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

            for col_idx, cell_value in enumerate(row_values):
                if cell_value is None:
                    continue

                field_name = col_mapping.get(col_idx)
                if not field_name:
                    continue

                # Format cell values cleanly
                if isinstance(cell_value, (datetime.datetime, datetime.date)):
                    formatted_val = cell_value.isoformat()
                elif isinstance(cell_value, float) and cell_value.is_integer():
                    formatted_val = str(int(cell_value))
                else:
                    formatted_val = str(cell_value).strip()

                if field_name == "description":
                    record["description"] = formatted_val
                elif field_name == "incident_type":
                    record["incident_type"] = ColumnMapper.normalize_incident_type(formatted_val)
                elif field_name == "date_time":
                    record["date_time"] = formatted_val
                else:
                    record[field_name] = formatted_val

            # Fallback only if no header column mapped to description
            if "description" not in col_mapping.values() and not record["description"]:
                text_cells = [str(c).strip() for c in row_values if c is not None and len(str(c).strip()) > 5]
                if text_cells:
                    record["description"] = max(text_cells, key=len)

            extracted_rows.append(record)

        return extracted_rows
