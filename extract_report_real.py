import openpyxl
import json

print("Loading workbook...")
wb = openpyxl.load_workbook('Forecast Semanal 2026 - Abril.xlsx', data_only=True, read_only=False)
sheet = wb["FORECAST"]

headers = [str(cell.value).strip() if cell.value is not None else "" for cell in sheet[3]]
print(f"Colunas encontradas: {len(headers)}")

cols = []
for i, h in enumerate(headers):
    if h:
        cols.append({'idx': i+1, 'col_letter': openpyxl.utils.get_column_letter(i+1), 'name': h})

sample_rows = []
for row_idx in range(4, 9):
    row_data = [str(cell.value).strip() if cell.value is not None else "" for cell in sheet[row_idx]]
    sample_rows.append(row_data)

cenarios = []
for h in headers:
    h_lower = h.lower()
    if 'orcado' in h_lower or 'orçado' in h_lower or 'forecast' in h_lower or 'previa' in h_lower or 'prévia' in h_lower or 'revisao' in h_lower or 'revisão' in h_lower:
        cenarios.append(h)

result = {
    'headers': cols,
    'scenarios': cenarios,
    'samples': sample_rows
}

with open('report_etapa1_real.json', 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print("Relatório salvo em report_etapa1_real.json")
