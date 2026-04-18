import sqlite3
import os
import openpyxl
from datetime import datetime

DB_PATH = os.environ.get(
    "DB_PATH",
    os.path.join(os.path.dirname(__file__), "..", "..", "data", "db", "previadb.db")
)
XLSX_PATH = os.environ.get(
    "XLSX_PATH",
    os.path.join(os.path.dirname(__file__), "..", "..", "data", "raw", "Forecast Semanal 2026 - Abril.xlsx")
)

def create_table_if_not_exists(conn):
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ajustamentos_gerencia (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            gerencia TEXT,
            resultado TEXT,
            cr_credito TEXT,
            cr_debito TEXT,
            mes_ref TEXT,
            incremento_credito REAL,
            justificativa TEXT,
            incremento_debito REAL,
            cr_envio TEXT,
            desc_cr_envio TEXT,
            gestor_cr_envio TEXT,
            cr_destino TEXT,
            desc_cr_destino TEXT,
            gestor_cr_destino TEXT,
            aba_origem TEXT
        )
    ''')
    conn.commit()
    ensure_aba_origem_column(conn)

def parse_float(val):
    if val is None:
        return 0.0
    try:
        if isinstance(val, (int, float)):
            return float(val)
        s = str(val).replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.')
        return float(s)
    except:
        return 0.0


def ensure_aba_origem_column(conn):
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(ajustamentos_gerencia)")
    columns = [row[1] for row in cursor.fetchall()]
    if 'aba_origem' not in columns:
        cursor.execute("ALTER TABLE ajustamentos_gerencia ADD COLUMN aba_origem TEXT")
        conn.commit()


def normalize_cr(value):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        if float(value).is_integer():
            return str(int(value)).strip()
        return str(value).strip()
    text = str(value).strip()
    if text.endswith('.0') and text[:-2].isdigit():
        return text[:-2]
    return text


def normalize_text(value):
    if value is None:
        return None
    return str(value).strip()


def load_sheet(conn, wb, sheet_name):
    if sheet_name not in wb.sheetnames:
        print(f"Aba {sheet_name} não encontrada.")
        return

    print(f"Carregando aba: {sheet_name}")
    sheet = wb[sheet_name]
    cursor = conn.cursor()

    count = 0

    if sheet_name == "GERENCIA EDILSON":
        for row in sheet.iter_rows(min_row=5, values_only=True):
            if not row[0]:
                continue

            resultado = normalize_text(row[0])
            cr_credito = normalize_cr(row[1])
            cr_debito = normalize_cr(row[2])
            mes_ref = None
            if isinstance(row[3], datetime):
                mes_ref = row[3].strftime('%Y-%m')
            elif row[3]:
                mes_ref = normalize_text(str(row[3])[:7])

            incremento_credito = parse_float(row[4])
            justificativa = normalize_text(row[5])
            incremento_debito = parse_float(row[6])
            cr_envio = normalize_cr(row[7])
            desc_cr_envio = normalize_text(row[8])
            gestor_cr_envio = normalize_text(row[9])
            cr_destino = normalize_cr(row[10])
            desc_cr_destino = normalize_text(row[11])
            gestor_cr_destino = normalize_text(row[12])

            cursor.execute('''
                INSERT INTO ajustamentos_gerencia (
                    gerencia, resultado, cr_credito, cr_debito, mes_ref,
                    incremento_credito, justificativa, incremento_debito,
                    cr_envio, desc_cr_envio, gestor_cr_envio,
                    cr_destino, desc_cr_destino, gestor_cr_destino, aba_origem
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                sheet_name, resultado, cr_credito, cr_debito, mes_ref,
                incremento_credito, justificativa, incremento_debito,
                cr_envio, desc_cr_envio, gestor_cr_envio,
                cr_destino, desc_cr_destino, gestor_cr_destino, sheet_name
            ))
            count += 1

    elif sheet_name == "GERENCIA OCTAVIO":
        for row in sheet.iter_rows(min_row=3, values_only=True):
            if not row[0]:
                continue

            resultado = normalize_text(row[0])
            cr_credito = normalize_cr(row[1])
            cr_debito = normalize_cr(row[2])
            mes_ref = None
            if isinstance(row[3], datetime):
                mes_ref = row[3].strftime('%Y-%m')
            elif row[3]:
                mes_ref = normalize_text(str(row[3])[:7])

            incremento_credito = parse_float(row[4])
            incremento_debito = parse_float(row[5])
            gestor_cr_destino = normalize_text(row[6])
            justificativa = normalize_text(row[7])

            cursor.execute('''
                INSERT INTO ajustamentos_gerencia (
                    gerencia, resultado, cr_credito, cr_debito, mes_ref,
                    incremento_credito, justificativa, incremento_debito,
                    cr_envio, desc_cr_envio, gestor_cr_envio,
                    cr_destino, desc_cr_destino, gestor_cr_destino, aba_origem
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                sheet_name, resultado, cr_credito, cr_debito, mes_ref,
                incremento_credito, justificativa, incremento_debito,
                None, None, None,
                None, None, gestor_cr_destino, sheet_name
            ))
            count += 1

    elif sheet_name == "GERENCIA WESLEY":
        for row in sheet.iter_rows(min_row=3, values_only=True):
            if not row[0]:
                continue
            if len(row) < 6:
                continue

            resultado = normalize_text(row[0])
            cr_credito = normalize_cr(row[1])
            cr_debito = normalize_cr(row[2])
            mes_ref = None
            if isinstance(row[3], datetime):
                mes_ref = row[3].strftime('%Y-%m')
            elif row[3]:
                mes_ref = normalize_text(str(row[3])[:7])

            incremento_credito = parse_float(row[4])
            incremento_debito = parse_float(row[5])
            justificativa = normalize_text(row[6]) if len(row) > 6 else None
            cr_envio = normalize_cr(row[7]) if len(row) > 7 else None
            desc_cr_envio = normalize_text(row[8]) if len(row) > 8 else None
            gestor_cr_envio = normalize_text(row[9]) if len(row) > 9 else None

            cursor.execute('''
                INSERT INTO ajustamentos_gerencia (
                    gerencia, resultado, cr_credito, cr_debito, mes_ref,
                    incremento_credito, justificativa, incremento_debito,
                    cr_envio, desc_cr_envio, gestor_cr_envio,
                    cr_destino, desc_cr_destino, gestor_cr_destino, aba_origem
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                sheet_name, resultado, cr_credito, cr_debito, mes_ref,
                incremento_credito, justificativa, incremento_debito,
                cr_envio, desc_cr_envio, gestor_cr_envio,
                None, None, None, sheet_name
            ))
            count += 1

    conn.commit()
    print(f"Abas '{sheet_name}': Inseridos {count} registros.")

if __name__ == "__main__":
    print(f"Iniciando ETL das gerencias a partir de {XLSX_PATH}")
    
    if not os.path.exists(XLSX_PATH):
        print(f"Arquivo não encontrado: {XLSX_PATH}")
        exit(1)
        
    wb = openpyxl.load_workbook(XLSX_PATH, read_only=True, data_only=True)
    
    conn = sqlite3.connect(DB_PATH)
    create_table_if_not_exists(conn)
    
    # Limpar a tabela antes de popular
    conn.execute("DELETE FROM ajustamentos_gerencia")
    conn.commit()
    
    gerencias = ["GERENCIA EDILSON", "GERENCIA OCTAVIO", "GERENCIA WESLEY"]
    
    for g in gerencias:
        load_sheet(conn, wb, g)
        
    conn.close()
    print("ETL concluído com sucesso.")
