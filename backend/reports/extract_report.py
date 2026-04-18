import os
import openpyxl
import json

xls_path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "raw", "Forecast Semanal 2026 - Abril.xlsx")
print("Carregando workbook...")
wb = openpyxl.load_workbook(xls_path, data_only=True, read_only=True)
sheet = wb["FORECAST"]

headers = [str(cell.value) if cell.value is not None else "" for cell in sheet[65]]
print(f"Colunas encontradas: {len(headers)}")

# Salva apenas cabeçalhos não-vazios e o seu índice (1-based)
cols = []
for i, h in enumerate(headers):
    # Pode haver alguns vazios, vamos guardar de toda forma
    cols.append({'idx': i+1, 'col_letter': openpyxl.utils.get_column_letter(i+1), 'name': h})

sample_rows = []
for row_idx in range(66, 71):
    row_data = [str(cell.value) if cell.value is not None else "" for cell in sheet[row_idx]]
    sample_rows.append(row_data)

cenarios = []
for h in headers:
    h_lower = h.lower()
    if 'orcado' in h_lower or 'orçado' in h_lower or 'forecast' in h_lower or 'previa' in h_lower or 'prévia' in h_lower:
        cenarios.append(h)

result = {
    'headers': cols,
    'scenarios': cenarios,
    'samples': sample_rows
}

output_path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "reports", "report_etapa1.json")
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print(f"Relatório salvo em {output_path}")
