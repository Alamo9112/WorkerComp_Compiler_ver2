import argparse
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from collections import defaultdict
from dataclasses import dataclass
from typing import List, Dict

try:
    import pdfplumber
except ImportError:  # pragma: no cover - pdfplumber may not be installed
    pdfplumber = None  # type: ignore

try:
    import pandas as pd
except ImportError:  # pragma: no cover - pandas may not be installed
    pd = None  # type: ignore

try:
    from openpyxl import Workbook
except ImportError:  # pragma: no cover - openpyxl may not be installed
    Workbook = None  # type: ignore

@dataclass
class EmployeeRecord:
    employee_code: str
    work_code: str
    regular_pay: float = 0.0
    overtime_pay: float = 0.0
    overtime_hours: float = 0.0

    @property
    def total_pay(self) -> float:
        return self.regular_pay + self.overtime_pay


def parse_pdf(path: str) -> List[Dict[str, str]]:
    """Parse a PDF file and return a list of row dicts.

    This function expects the PDF to contain a table where the first row is the
    header. Columns should include at least ``Name`` and ``Pay Type`` along with
    ``Hours`` and ``Amount``. Additional columns are ignored.
    """
    if pdfplumber is None:
        raise RuntimeError("pdfplumber is required to parse PDF files")

    rows: List[Dict[str, str]] = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            table = page.extract_table()
            if not table:
                continue
            headers = [h.strip() if h else "" for h in table[0]]
            for line in table[1:]:
                row = {headers[i]: (line[i] or "").strip() for i in range(len(headers))}
                rows.append(row)
    return rows


def compile_records(rows: List[Dict[str, str]]) -> Dict[str, EmployeeRecord]:
    """Compile raw rows into per employee records."""
    employees: Dict[str, EmployeeRecord] = defaultdict(lambda: EmployeeRecord("", ""))
    for row in rows:
        name = row.get("Name") or row.get("Employee") or row.get("Employee Name")
        if not name:
            continue
        record = employees[name]
        if not record.employee_code:
            record.employee_code = row.get("Employee Code", "")
        if not record.work_code:
            record.work_code = row.get("Work Code", "")

        pay_type = (row.get("Pay Type") or "").lower()
        hours = float(row.get("Hours", 0) or 0)
        amount = float(row.get("Amount", 0) or 0)
        if "ot" in pay_type or "overtime" in pay_type:
            record.overtime_hours += hours
            record.overtime_pay += amount
        else:
            record.regular_pay += amount
    return employees


def write_excel(records: Dict[str, EmployeeRecord], path: str) -> None:
    """Write compiled records to an Excel file."""
    if pd is not None:
        data = [
            {
                "Name": name,
                "Employee Code": rec.employee_code,
                "Work Code": rec.work_code,
                "Pay": rec.total_pay,
                "OT Hours": rec.overtime_hours,
                "Tips": 0,
            }
            for name, rec in records.items()
        ]
        df = pd.DataFrame(data)
        df.to_excel(path, index=False)
        return

    if Workbook is None:
        raise RuntimeError(
            "openpyxl or pandas is required to write Excel output"
        )

    wb = Workbook()
    ws = wb.active
    ws.append(["Name", "Employee Code", "Work Code", "Pay", "OT Hours", "Tips"])
    for name, rec in records.items():
        ws.append([
            name,
            rec.employee_code,
            rec.work_code,
            rec.total_pay,
            rec.overtime_hours,
            0,
        ])
    wb.save(path)

def show_pdf_with_grid(pdf_path: str, page_num: int = 0, rows: int = 4, cols: int = 4):
    if pdfplumber is None:
        raise RuntimeError("pdfplumber is required for this feature")

    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[page_num]
        im = page.to_image(resolution=150)

        fig, ax = plt.subplots(figsize=(10, 14))
        ax.imshow(im.original)

        width, height = page.width, page.height
        col_width = width / cols
        row_height = height / rows

        for i in range(1, cols):
            ax.add_line(plt.Line2D([i * col_width, i * col_width], [0, height], color='red', linewidth=1))
        for j in range(1, rows):
            ax.add_line(plt.Line2D([0, width], [j * row_height, j * row_height], color='red', linewidth=1))

        for r in range(rows):
            for c in range(cols):
                x0 = c * col_width
                y0 = r * row_height
                x1 = x0 + col_width
                y1 = y0 + row_height
                bbox = (x0, y0, x1, y1)
                text = page.within_bbox(bbox).extract_text() or ""
                print(f"Cell ({r+1},{c+1}):", repr(text.strip()))
                rect = patches.Rectangle((x0, y0), col_width, row_height,
                                         linewidth=1, edgecolor='blue', facecolor='none')
                ax.add_patch(rect)

        ax.set_xlim(0, width)
        ax.set_ylim(height, 0)
        plt.title(f"Grid Overlay ({rows}x{cols}) on Page {page_num + 1}")
        plt.axis("off")
        plt.show()

def main() -> None:
    parser = argparse.ArgumentParser(description="Compile employee register PDF into Excel")
    parser.add_argument("pdf", help="Input PDF file")
    parser.add_argument("output", help="Output Excel file (.xlsx)")
    args = parser.parse_args()

    rows = parse_pdf(args.pdf)
    records = compile_records(rows)
    write_excel(records, args.output)


if __name__ == "__main__":
    main()