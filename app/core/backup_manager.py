import json
import zipfile
import tempfile
import shutil
from pathlib import Path

# Tables to backup. We EXCLUDE: ai_providers, api_keys_metadata, models, ai_events, usage_info.
TABLES_TO_BACKUP = [
    "projects", "project_documents", "profile", "skills", "achievements", "posts",
    "memories", "conversations", "certificates", "hackathons", 
    "linkedin_data", "linkedin_posts", "linkedin_certificates", 
    "linkedin_projects", "linkedin_skills", "linkedin_languages",
    "github_data", "media_attachments"
]

def export_data(db_manager, output_zip_path):
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        data_file = tmp_path / "forgehub_data.json"
        
        backup_data = {}
        with db_manager.get_connection() as conn:
            conn.row_factory = None # Need raw tuples or dicts
            cursor = conn.cursor()
            
            for table in TABLES_TO_BACKUP:
                try:
                    # Get column names
                    cursor.execute(f"PRAGMA table_info({table})")
                    columns = [row[1] for row in cursor.fetchall()]
                    
                    if not columns:
                        continue
                        
                    # Get all rows
                    cursor.execute(f"SELECT * FROM {table}")
                    rows = cursor.fetchall()
                    
                    # Convert to list of dicts
                    table_data = []
                    for row in rows:
                        table_data.append(dict(zip(columns, row)))
                        
                    backup_data[table] = table_data
                except Exception as e:
                    print(f"Error exporting table {table}: {e}")
                    
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, indent=2)
            
        # Create ZIP file
        with zipfile.ZipFile(output_zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.write(data_file, "forgehub_data.json")

def import_data(db_manager, input_zip_path):
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        
        try:
            with zipfile.ZipFile(input_zip_path, 'r') as zf:
                zf.extractall(tmp_path)
        except zipfile.BadZipFile:
            raise ValueError("The selected file is not a valid zip archive.")
            
        data_file = tmp_path / "forgehub_data.json"
        if not data_file.exists():
            raise ValueError("The backup zip does not contain forgehub_data.json.")
            
        with open(data_file, 'r', encoding='utf-8') as f:
            try:
                backup_data = json.load(f)
            except json.JSONDecodeError:
                raise ValueError("The backup data file is corrupted or unreadable.")
                
        # Validate structure roughly
        if not isinstance(backup_data, dict):
            raise ValueError("Invalid data structure in backup file.")
            
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # Disable foreign keys temporarily during import
            conn.execute("PRAGMA foreign_keys = OFF")
            
            try:
                # 1. Clear existing data for these tables ONLY
                for table in TABLES_TO_BACKUP:
                    if table in backup_data:
                        try:
                            cursor.execute(f"DELETE FROM {table}")
                        except Exception as e:
                            print(f"Could not clear {table}: {e}")
                            
                # 2. Insert new data
                for table, rows in backup_data.items():
                    if not rows or table not in TABLES_TO_BACKUP:
                        continue
                        
                    columns = list(rows[0].keys())
                    placeholders = ", ".join(["?"] * len(columns))
                    cols_str = ", ".join(columns)
                    
                    insert_query = f"INSERT INTO {table} ({cols_str}) VALUES ({placeholders})"
                    
                    data_to_insert = []
                    for row in rows:
                        data_to_insert.append(tuple(row.get(c) for c in columns))
                        
                    try:
                        cursor.executemany(insert_query, data_to_insert)
                    except Exception as e:
                        print(f"Error inserting into {table}: {e}")
                        
                conn.commit()
            except Exception as e:
                conn.rollback()
                raise e
            finally:
                conn.execute("PRAGMA foreign_keys = ON")
