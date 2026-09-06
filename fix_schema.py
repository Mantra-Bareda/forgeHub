import sqlite3

conn = sqlite3.connect('database/forgehub.db')
cursor = conn.cursor()
try:
    cursor.execute("ALTER TABLE models ADD COLUMN key_id INTEGER REFERENCES api_keys_metadata(id)")
except sqlite3.OperationalError:
    pass

# We will clear the models table so they can be re-fetched cleanly with key_ids
cursor.execute("DELETE FROM models")
conn.commit()
conn.close()
print("Schema updated for per-key models.")
