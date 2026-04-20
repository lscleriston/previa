import sqlite3
import os
from datetime import datetime

DB_PATH = os.environ.get(
    "DB_PATH",
    os.path.join(os.path.dirname(__file__), "..", "..", "data", "db", "previadb.db")
)

def init_db():
    print(f"Criando o banco de dados em: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Criar tabela principal de oportunidades
    cursor.executescript("""
    CREATE TABLE IF NOT EXISTS forecast_oportunidades (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chave_ek TEXT UNIQUE,
        data_criacao DATE,
        banco TEXT,
        ano INTEGER,
        pais TEXT,
        tipo_papel TEXT,
        gerente TEXT,
        owner TEXT,
        ger_comercial TEXT,
        operacao TEXT,
        ger_operacao TEXT,
        pre_vendas TEXT,
        pratica TEXT,
        produto TEXT,
        id_empresa TEXT,
        cliente TEXT,
        cliente_ge TEXT,
        subcliente TEXT,
        novo_cliente BOOLEAN,
        industria TEXT,
        id_oportunidade TEXT,
        descricao_oportunidade TEXT,
        status_comercial TEXT,
        status_comercial_det TEXT,
        metodologia TEXT,
        tipo_opp TEXT,
        cr TEXT,
        cr2 TEXT,
        semana_fechamento TEXT,
        cr_oi TEXT,
        ordem_interna TEXT,
        moeda TEXT,
        consideracao TEXT,
        vigencia TEXT,
        contrato TEXT,
        data_inicio_contrato DATE,
        data_fim_contrato DATE,
        mes_reajuste TEXT,
        risco TEXT,
        deducao REAL,
        pct_ponderacao REAL,
        semana_carga DATETIME,
        arquivo_origem TEXT
    );

    CREATE TABLE IF NOT EXISTS forecast_valores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chave_ek TEXT,
        cenario TEXT,
        mes_ref TEXT,
        valor_rl REAL,
        valor_rb REAL,
        semana_carga DATETIME,
        FOREIGN KEY (chave_ek) REFERENCES forecast_oportunidades(chave_ek)
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

    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        is_admin INTEGER NOT NULL DEFAULT 0,
        created_at TEXT NOT NULL
    );
    """)
    
    def ensure_user(username, password, is_admin=False):
        cursor.execute("SELECT COUNT(*) FROM users WHERE username = ?", (username,))
        if cursor.fetchone()[0] == 0:
            from passlib.context import CryptContext
            pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
            password_hash = pwd_context.hash(password)
            cursor.execute(
                "INSERT INTO users (username, password_hash, is_admin, created_at) VALUES (?, ?, ?, ?)",
                (username, password_hash, 1 if is_admin else 0, datetime.utcnow().isoformat())
            )
            print(f"Usuário '{username}' criado com senha '{password}'.")
        else:
            print(f"Usuário '{username}' já existe. Pulando criação.")

    ensure_user("admin", "admin", is_admin=True)
    ensure_user("cleristonls", "senha123", is_admin=True)
    
    conn.commit()
    conn.close()
    print("Tabelas criadas com sucesso no banco de dados previadb.db!")

if __name__ == "__main__":
    init_db()
