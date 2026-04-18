import os
import sqlite3

DB_PATH = os.environ.get(
    "DB_PATH",
    os.path.join(os.path.dirname(__file__), "..", "..", "data", "db", "previadb.db")
)
c = sqlite3.connect(DB_PATH).cursor()
res = c.execute("SELECT Cod_Cr, COUNT(1) FROM dim_cr GROUP BY Cod_Cr").fetchall()
print([r for r in res if r[1] > 1])
