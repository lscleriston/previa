import os
import sqlite3

DB_PATH = os.environ.get(
    "DB_PATH",
    os.path.join(os.path.dirname(__file__), "..", "..", "data", "db", "previadb.db")
)
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()
query = "SELECT d.Cod_Cr as cr, COUNT(DISTINCT o.id) as qtd_opp, SUM(CASE WHEN v.cenario='Forecast' THEN v.valor_rl ELSE 0 END) as total_rl FROM forecast_oportunidades o LEFT JOIN forecast_valores v ON o.chave_ek = v.chave_ek LEFT JOIN dim_cr d ON o.cr = d.Cod_Cr WHERE 1=1  AND d.Gerente='Cleriston Lopes Silva' AND v.mes_ref='2026-04' GROUP BY d.Cod_Cr"
print(c.execute(query).fetchall())
