import sqlite3
c = sqlite3.connect('data/previadb.db').cursor()
res = c.execute("SELECT Cod_Cr, COUNT(1) FROM dim_cr GROUP BY Cod_Cr").fetchall()
print([r for r in res if r[1] > 1])
