import sqlite3

good_models = [
    "gemini-1.5-pro", "gemini-1.5-flash", "gemini-2.0-pro-exp", "gemini-2.5-pro", 
    "llama3-70b-8192", "llama3-8b-8192", "mixtral-8x7b-32768", "gemma2-9b-it",
    "mistral-large-latest", "mistral-small-latest", "open-mixtral-8x22b",
    "llama3.1-8b", "llama3.1-70b", "llama-3.3-70b-versatile"
]

conn = sqlite3.connect('database/forgehub.db')
cursor = conn.cursor()
cursor.execute("UPDATE models SET is_enabled = 0")
for g in good_models:
    cursor.execute("UPDATE models SET is_enabled = 1 WHERE model_id LIKE ?", (f'%{g}%',))
conn.commit()
conn.close()
