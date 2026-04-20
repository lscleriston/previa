import sqlite3
import os
from datetime import datetime

# Mantendo o padrão do projeto, o DB_PATH aponta para o banco de dados existente.
DB_PATH = os.environ.get("DB_PATH", os.path.join('data', 'db', 'previadb.db'))

def create_users_table(conn):
    """Cria a tabela de usuários se ela não existir."""
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            is_admin INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL
        )
    ''')
    conn.commit()
    print("Tabela 'users' verificada/criada com sucesso.")

def create_initial_admin_user(conn):
    """Cria um usuário 'admin' inicial se nenhum usuário existir."""
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        username = "admin"
        password = "admin" # Senha provisória
        password_hash = pwd_context.hash(password)
        created_at = datetime.utcnow().isoformat()
        
        cursor.execute(
            "INSERT INTO users (username, password_hash, is_admin, created_at) VALUES (?, ?, ?, ?)",
            (username, password_hash, 1, created_at)
        )
        conn.commit()
        print(f"Usuário administrador inicial '{username}' criado com a senha provisória '{password}'.")
        print("IMPORTANTE: Altere esta senha em um ambiente de produção.")
    else:
        print("O banco de dados já contém usuários. Nenhum usuário inicial foi criado.")


if __name__ == "__main__":
    print(f"Conectando ao banco de dados em: {DB_PATH}")
    
    # Garante que o diretório do banco de dados exista
    db_dir = os.path.dirname(DB_PATH)
    if not os.path.exists(db_dir):
        os.makedirs(db_dir)
        print(f"Diretório '{db_dir}' criado.")

    conn = sqlite3.connect(DB_PATH)
    try:
        create_users_table(conn)
        create_initial_admin_user(conn)
    finally:
        conn.close()
        print("Conexão com o banco de dados fechada.")
