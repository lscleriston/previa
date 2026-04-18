import os
import openpyxl

xlsx_path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "raw", "Forecast Semanal 2026 - Abril.xlsx")
print("Loading...")
wb = openpyxl.load_workbook(xlsx_path, read_only=True, data_only=True)
sheet = wb['FORECAST']
print("Scanning rows...")
for i, row in enumerate(sheet.iter_rows(max_row=100, values_only=True), start=1):
    for c in row:
        if isinstance(c, str) and 'oportunidade' in c.lower():
            print(f"Header possibly at row {i}")
            print(f"Sample: {row[:15]}")
            break
print("Done")