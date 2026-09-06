import sqlite3
conn = sqlite3.connect('database/forgehub.db')
cursor = conn.cursor()
try:
    cursor.execute("ALTER TABLE models ADD COLUMN is_enabled INTEGER DEFAULT 1")
    cursor.execute("ALTER TABLE models ADD COLUMN rpm_limit INTEGER DEFAULT NULL")
    cursor.execute("ALTER TABLE models ADD COLUMN rpd_limit INTEGER DEFAULT NULL")
    conn.commit()
    print("Migration successful")
except sqlite3.OperationalError as e:
    print("Migration error (might already exist):", e)
conn.close()
