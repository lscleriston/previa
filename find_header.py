import openpyxl

print("Loading...")
wb = openpyxl.load_workbook('Forecast Semanal 2026 - Abril.xlsx', read_only=True, data_only=True)
sheet = wb['FORECAST']
print("Scanning rows...")
for i, row in enumerate(sheet.iter_rows(max_row=100, values_only=True), start=1):
    for c in row:
        if isinstance(c, str) and 'oportunidade' in c.lower():
            print(f"Header possibly at row {i}")
            print(f"Sample: {row[:15]}")
            break
print("Done")