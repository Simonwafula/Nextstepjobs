import sqlite3

RAW_DB    = "db/jobs.sqlite3"
RAW_TABLE = "jobs_data"
STRUCT_DB    = "db/test_struct.sqlite3"
STRUCT_TABLE = "test_struct"

# 1) Read a handful of rows
conn = sqlite3.connect(RAW_DB)
cur  = conn.cursor()
cur.execute(f"SELECT id, content FROM {RAW_TABLE} LIMIT 3")
rows = cur.fetchall()
conn.close()
print("RAW ROWS:", rows)

# 2) Write a dummy structured table
conn = sqlite3.connect(STRUCT_DB)
conn.execute(f"CREATE TABLE IF NOT EXISTS {STRUCT_TABLE} (id INT, json TEXT)")
conn.executemany(
    f"INSERT INTO {STRUCT_TABLE} (id,json) VALUES (?,?)",
    [(r[0], '{"dummy":true}') for r in rows]
)
conn.commit()

# 3) Read it back
cur = conn.cursor()
cur.execute(f"SELECT * FROM {STRUCT_TABLE}")
print("STRUCT ROWS:", cur.fetchall())
conn.close()
