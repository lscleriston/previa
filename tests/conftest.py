import asyncio
import os
import sqlite3
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if (ROOT_DIR / 'backend').exists():
    sys.path.insert(0, str(ROOT_DIR))
elif Path('/app/backend').exists():
    sys.path.insert(0, '/app')

import pytest
from httpx import AsyncClient, ASGITransport
from openpyxl import Workbook

import backend.api.routes.upload as upload
import backend.db.database as database
from backend.api.app import app


@pytest.fixture(scope="session")
def api_base_url():
    if os.path.exists('/.dockerenv') or os.path.exists('/run/.containerenv'):
        return "http://backend:8000"
    return "http://localhost:8000"


@pytest.fixture(scope="session")
def frontend_base_url():
    if os.path.exists('/.dockerenv') or os.path.exists('/run/.containerenv'):
        return "http://frontend"
    return "http://localhost:3000"


@pytest.fixture(scope="session")
def test_db_path(tmp_path_factory):
    db_dir = tmp_path_factory.mktemp("test_data")
    db_path = db_dir / "previadb.db"

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.executescript("""
    CREATE TABLE IF NOT EXISTS forecast_oportunidades (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chave_ek TEXT UNIQUE,
        cr TEXT,
        pratica TEXT,
        produto TEXT,
        cliente TEXT,
        gerente TEXT,
        pais TEXT
    );

    CREATE TABLE IF NOT EXISTS forecast_valores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chave_ek TEXT,
        cenario TEXT,
        mes_ref TEXT,
        valor_rl REAL,
        valor_rb REAL
    );

    CREATE TABLE IF NOT EXISTS etl_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        arquivo TEXT,
        aba TEXT,
        linhas_lidas INTEGER,
        linhas_carregadas INTEGER,
        linhas_ignoradas INTEGER,
        status TEXT,
        mensagem TEXT,
        executado_em DATETIME
    );

    CREATE TABLE IF NOT EXISTS previa_folha_th (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        mes_ref TEXT,
        cr TEXT,
        cliente TEXT,
        valor REAL,
        fonte TEXT
    );

    CREATE TABLE IF NOT EXISTS rateio_automatico (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cr TEXT,
        mes_ref TEXT,
        rateio REAL,
        cr_envio TEXT,
        desc_cr_envio TEXT,
        gestor_cr_envio TEXT,
        cliente TEXT,
        rl_rateio TEXT,
        descricao TEXT,
        aba_origem TEXT
    );

    CREATE TABLE IF NOT EXISTS dim_cr (
        Cod_Cr TEXT PRIMARY KEY,
        CR_SAP TEXT UNIQUE,
        Cliente TEXT,
        Des_CR TEXT,
        Pais TEXT,
        Diretor TEXT,
        Gerente TEXT
    );

    CREATE TABLE IF NOT EXISTS ajustamentos_gerencia (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        gerencia TEXT,
        resultado TEXT,
        cr_credito TEXT,
        cr_debito TEXT,
        mes_ref TEXT,
        incremento_credito REAL,
        incremento_debito REAL,
        justificativa TEXT,
        cr_envio TEXT,
        desc_cr_envio TEXT,
        gestor_cr_envio TEXT,
        cr_destino TEXT,
        desc_cr_destino TEXT,
        gestor_cr_destino TEXT,
        aba_origem TEXT
    );

    CREATE TABLE IF NOT EXISTS orcamento_previa (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cr TEXT,
        mes_ref TEXT,
        categoria_despesa TEXT,
        valor_plano REAL
    );
    """)

    cursor.execute(
        "INSERT INTO dim_cr (Cod_Cr, CR_SAP, Cliente, Des_CR, Pais, Diretor, Gerente) VALUES (?, ?, ?, ?, ?, ?, ?)",
        ("CR-001", None, "Cliente Teste", "CR Teste", "Brasil", "DIRETOR TESTE", "GERENTE TESTE"),
    )
    cursor.execute(
        "INSERT INTO dim_cr (Cod_Cr, CR_SAP, Cliente, Des_CR, Pais, Diretor, Gerente) VALUES (?, ?, ?, ?, ?, ?, ?)",
        ("CR-002", None, "Cliente Dois", "CR Dois", "Brasil", "DIRETOR TESTE", "GERENTE TESTE"),
    )
    cursor.execute(
        "INSERT INTO dim_cr (Cod_Cr, CR_SAP, Cliente, Des_CR, Pais, Diretor, Gerente) VALUES (?, ?, ?, ?, ?, ?, ?)",
        ("CR-003", None, "Cliente Tres", "CR Tres", "Brasil", "DIRETOR TESTE", "GERENTE TESTE"),
    )

    cursor.execute(
        "INSERT INTO forecast_oportunidades (chave_ek, cr, pratica, produto, cliente, gerente, pais) VALUES (?, ?, ?, ?, ?, ?, ?)",
        ("EK-001", "CR-001", "Pratica X", "Produto Y", "Cliente Teste", "GERENTE TESTE", "Brasil"),
    )
    cursor.execute(
        "INSERT INTO forecast_oportunidades (chave_ek, cr, pratica, produto, cliente, gerente, pais) VALUES (?, ?, ?, ?, ?, ?, ?)",
        ("EK-002", "CR-002", "Pratica X", "Produto Z", "Cliente Dois", "GERENTE TESTE", "Brasil"),
    )
    cursor.execute(
        "INSERT INTO forecast_oportunidades (chave_ek, cr, pratica, produto, cliente, gerente, pais) VALUES (?, ?, ?, ?, ?, ?, ?)",
        ("EK-003", "CR-003", "Pratica X", "Produto W", "Cliente Tres", "GERENTE TESTE", "Brasil"),
    )

    cursor.execute(
        "INSERT INTO forecast_valores (chave_ek, cenario, mes_ref, valor_rl, valor_rb) VALUES (?, ?, ?, ?, ?)",
        ("EK-001", "Forecast", "2026-04", 10000.0, 9800.0),
    )
    cursor.execute(
        "INSERT INTO forecast_valores (chave_ek, cenario, mes_ref, valor_rl, valor_rb) VALUES (?, ?, ?, ?, ?)",
        ("EK-002", "Forecast", "2026-04", 8000.0, 7800.0),
    )
    cursor.execute(
        "INSERT INTO forecast_valores (chave_ek, cenario, mes_ref, valor_rl, valor_rb) VALUES (?, ?, ?, ?, ?)",
        ("EK-003", "Forecast", "2026-04", 5000.0, 4900.0),
    )

    cursor.execute(
        "INSERT INTO ajustamentos_gerencia (gerencia, resultado, cr_credito, cr_debito, mes_ref, incremento_credito, incremento_debito, justificativa, cr_envio, desc_cr_envio, gestor_cr_envio, cr_destino, desc_cr_destino, gestor_cr_destino, aba_origem) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        ("GERENTE TESTE", "Recuperação Pessoal", "CR-001", None, "2026-04", 500.0, 0.0, "Teste recuperação pessoal", None, "Origem CR", "Responsável", None, None, None, "TESTE"),
    )

    cursor.execute(
        "INSERT INTO ajustamentos_gerencia (gerencia, resultado, cr_credito, cr_debito, mes_ref, incremento_credito, incremento_debito, justificativa, cr_envio, desc_cr_envio, gestor_cr_envio, cr_destino, desc_cr_destino, gestor_cr_destino, aba_origem) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        ("GERENTE TESTE", "Recuperação Pessoal", None, "CR-003", "2026-04", 0.0, -250.0, "Teste débito recuperação", None, None, None, None, None, None, "TESTE"),
    )

    conn.commit()
    conn.close()

    database.DB_PATH = str(db_path)
    upload.DB_PATH = str(db_path)
    os.environ["DB_PATH"] = str(db_path)

    return str(db_path)


@pytest.fixture
def api_client(test_db_path):
    client = AsyncClient(app=app, base_url="http://localhost:8000", transport=ASGITransport(app=app))
    yield client
    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(client.aclose())
    finally:
        loop.close()


@pytest.fixture
def xlsx_file(tmp_path):
    path = tmp_path / "test_upload.xlsx"
    wb = Workbook()
    ws = wb.active
    ws.title = "Dados de Upload"
    ws.append(["Coluna A", "Coluna B", "Coluna C", "Coluna D"])
    for index in range(10):
        ws.append([f"CR-{index:03}", index * 10, f"Descrição {index}", "Teste"])
    wb.save(path)
    return str(path)
