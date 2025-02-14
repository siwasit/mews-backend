from openpyxl import load_workbook
from openpyxl.styles import Border, Side

class ExcelDecorator:
    def __init__(self, filepath: str):
        self.filepath = filepath

    def decorate(self):
        wb = load_workbook(self.filepath)
        ws = wb.active
        ws.delete_rows(1)

        # Define border style (thin black lines)
        thin_border = Border(
            left=Side(style="thin"),
            right=Side(style="thin"),
            top=Side(style="thin"),
            bottom=Side(style="thin")
        )

        # Find the last row with content
        last_row = ws.max_row  # This will get the last row with any content

        # Apply borders from A8 to L (all rows with content)
        for row in range(7, last_row + 1):  # Start from row 8
            for col in range(1, 13):  # Columns A (1) to L (12)
                cell = ws.cell(row=row, column=col)
                cell.border = thin_border

        # Save the updated Excel file
        wb.save(self.filepath)
        wb.close()

# Usage example:
# file_path = "styled_report.xlsx"
# decorator = ExcelDecorator(file_path)
# decorator.decorate()