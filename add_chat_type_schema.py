import sqlite3

def update_schema():
    conn = sqlite3.connect('database/forgehub.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute("ALTER TABLE conversations ADD COLUMN chat_context TEXT DEFAULT 'general'")
    except sqlite3.OperationalError:
        pass # Column already exists
        
    conn.commit()
    conn.close()
    print("Schema updated for Chat Context.")

if __name__ == "__main__":
    update_schema()
