import sqlite3

def update_schema():
    conn = sqlite3.connect('database/forgehub.db')
    cursor = conn.cursor()
    
    # LinkedIn table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS linkedin_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        bio TEXT,
        about TEXT,
        posts TEXT,
        certificates TEXT,
        projects TEXT,
        languages TEXT,
        skills TEXT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Insert default row if not exists
    cursor.execute("SELECT COUNT(*) FROM linkedin_data")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO linkedin_data (username) VALUES ('')")
        
    # GitHub table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS github_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        profile_readme TEXT,
        projects_summary TEXT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Insert default row if not exists
    cursor.execute("SELECT COUNT(*) FROM github_data")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO github_data (username) VALUES ('')")

    conn.commit()
    conn.close()
    print("Schema updated for LinkedIn and GitHub.")

if __name__ == "__main__":
    update_schema()
