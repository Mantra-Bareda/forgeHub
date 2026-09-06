import sqlite3

conn = sqlite3.connect('database/forgehub.db')
cursor = conn.cursor()
try:
    cursor.execute("ALTER TABLE profile ADD COLUMN ai_overview TEXT")
    conn.commit()
    print("Added ai_overview column.")
except sqlite3.OperationalError as e:
    print("Column might exist:", e)
conn.close()
