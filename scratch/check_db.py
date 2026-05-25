import sqlite3

conn = sqlite3.connect("/Users/satwikmedipalli/Project2/data/nfl_teams.db")
cur = conn.cursor()

# Check play_by_play columns
cur.execute("PRAGMA table_info(play_by_play)")
cols = cur.fetchall()
col_names = [c[1] for c in cols]
print("All play_by_play columns:")
print(col_names)

print("\nAll contracts columns:")
cur.execute("PRAGMA table_info(contracts)")
print([c[1] for c in cur.fetchall()])

conn.close()
