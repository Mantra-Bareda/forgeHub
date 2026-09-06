import sqlite3

def update_schema():
    conn = sqlite3.connect('database/forgehub.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute("ALTER TABLE linkedin_data ADD COLUMN ai_insights TEXT")
    except sqlite3.OperationalError:
        pass # Column already exists

    try:
        cursor.execute("ALTER TABLE github_data ADD COLUMN ai_insights TEXT")
    except sqlite3.OperationalError:
        pass
        
    conn.commit()
    conn.close()
    print("Schema updated for AI Insights.")

if __name__ == "__main__":
    update_schema()
