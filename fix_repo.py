import re

with open('database/repository.py', 'r') as f:
    content = f.read()

# Add keyring import at top
if "import keyring" not in content:
    content = "import sqlite3\n" + """
try:
    import keyring
except ImportError:
    keyring = None
""" + content.replace('import sqlite3\n', '')

start_idx = content.find("class ProviderRepository(Repository):")
end_idx = content.find("class ChatRepository(Repository):")

new_provider_repo = """class ProviderRepository(Repository):
    def initialize_providers(self):
        providers = ["Gemini", "Groq", "Mistral", "Cerebras"]
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            for p in providers:
                cursor.execute("INSERT OR IGNORE INTO ai_providers (name) VALUES (?)", (p,))
            conn.commit()

    def get_providers(self):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(\"\"\"
                SELECT p.id, p.name, p.status, 
                       k.id as key_id, k.api_key, k.last_tested, k.key_slot, k.enabled, k.display_name, k.status as key_status
                FROM ai_providers p
                LEFT JOIN api_keys_metadata k ON p.id = k.provider_id
            \"\"\")
            rows = cursor.fetchall()
            
            providers_dict = {}
            for row in rows:
                p_name = row["name"]
                if p_name not in providers_dict:
                    providers_dict[p_name] = {
                        "id": row["id"],
                        "name": p_name,
                        "status": row["status"],
                        "keys": {}
                    }
                
                if row["key_id"]:
                    key_val = row["api_key"]
                    if keyring:
                        try:
                            kr_val = keyring.get_password("forgehub", f"api_key_{row['key_id']}")
                            if kr_val: key_val = kr_val
                        except Exception:
                            pass
                    
                    providers_dict[p_name]["keys"][row["key_slot"]] = {
                        "id": row["key_id"],
                        "api_key": key_val,
                        "last_tested": row["last_tested"],
                        "key_slot": row["key_slot"],
                        "enabled": row["enabled"],
                        "display_name": row["display_name"],
                        "status": row["key_status"]
                    }
            
            return list(providers_dict.values())

    def save_api_key(self, provider_name, api_key, status="Valid", key_slot=1, display_name=None, enabled=1):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM ai_providers WHERE name = ?", (provider_name,))
            provider = cursor.fetchone()
            if not provider: return

            cursor.execute("SELECT id FROM api_keys_metadata WHERE provider_id = ? AND key_slot = ?", (provider["id"], key_slot))
            existing_key = cursor.fetchone()
            
            disp_name = display_name if display_name else f"{provider_name} Key {key_slot}"
            
            if existing_key:
                key_id = existing_key["id"]
                db_api_key = "••••••••" if keyring and api_key != "••••••••" else api_key
                if db_api_key == "••••••••":
                    pass
                else:
                    db_api_key = db_api_key

                update_key_str = ""
                params = [status, disp_name, enabled, key_id]
                if api_key != "••••••••":
                    update_key_str = "api_key = ?,"
                    params.insert(0, db_api_key)

                cursor.execute(f\"\"\"
                    UPDATE api_keys_metadata 
                    SET {update_key_str} status = ?, last_tested = CURRENT_TIMESTAMP, display_name = ?, enabled = ?
                    WHERE id = ?
                \"\"\", tuple(params))
            else:
                db_api_key = "••••••••" if keyring else api_key
                cursor.execute(\"\"\"
                    INSERT INTO api_keys_metadata (provider_id, display_name, api_key, status, last_tested, key_slot, enabled)
                    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, ?, ?)
                \"\"\", (provider["id"], disp_name, db_api_key, status, key_slot, enabled))
                key_id = cursor.lastrowid
                
            cursor.execute("UPDATE ai_providers SET status = ? WHERE id = ?", (status, provider["id"]))
            conn.commit()
            
            if keyring and api_key != "••••••••":
                try:
                    keyring.set_password("forgehub", f"api_key_{key_id}", api_key)
                except Exception:
                    pass
            
            return key_id

    def delete_api_key(self, key_id):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM api_keys_metadata WHERE id = ?", (key_id,))
            conn.commit()
            if keyring:
                try:
                    keyring.delete_password("forgehub", f"api_key_{key_id}")
                except Exception:
                    pass

    def save_models(self, provider_name, models_list):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM ai_providers WHERE name = ?", (provider_name,))
            provider = cursor.fetchone()
            if not provider: return
            
            # Clear old models for this provider
            cursor.execute("DELETE FROM models WHERE provider_id = ?", (provider["id"],))
            
            for m in models_list:
                cursor.execute(\"\"\"
                    INSERT INTO models (provider_id, model_id, name, context_size, category, availability)
                    VALUES (?, ?, ?, ?, ?, ?)
                \"\"\", (provider["id"], m["model_id"], m["name"], m["context_size"], m["category"], m["availability"]))
            
            conn.commit()
            
    def get_models(self, provider_name=None):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            if provider_name:
                cursor.execute(\"\"\"
                    SELECT m.* FROM models m
                    JOIN ai_providers p ON m.provider_id = p.id
                    WHERE p.name = ?
                \"\"\", (provider_name,))
            else:
                cursor.execute("SELECT * FROM models")
            return [dict(row) for row in cursor.fetchall()]

    def get_available_models(self, category=None):
        \"\"\"Fetches all dynamically discovered models that have valid API keys attached.\"\"\"
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            query = \"\"\"
                SELECT m.model_id, m.name, m.context_size, m.category, 
                       p.name as provider_name, k.api_key, k.id as key_id 
                FROM models m
                JOIN ai_providers p ON m.provider_id = p.id
                JOIN api_keys_metadata k ON p.id = k.provider_id
                WHERE k.enabled = 1 AND k.status NOT IN ('Invalid Key', 'Not Configured')
            \"\"\"
            params = []
            if category:
                query += " AND m.category = ?"
                params.append(category)
            
            cursor.execute(query, params)
            rows = [dict(row) for row in cursor.fetchall()]
            
            for row in rows:
                if keyring:
                    try:
                        kr_val = keyring.get_password("forgehub", f"api_key_{row['key_id']}")
                        if kr_val: row["api_key"] = kr_val
                    except Exception:
                        pass
            return rows

"""

content = content[:start_idx] + new_provider_repo + content[end_idx:]

with open('database/repository.py', 'w') as f:
    f.write(content)
print("Updated database/repository.py")
