import sqlite3

try:
    import keyring
except ImportError:
    keyring = None

class Repository:
    def __init__(self, db_manager):
        self.db = db_manager

class ProjectRepository(Repository):
    # --- Projects ---
    def create_project(self, name, description="", tech_stack="", status="Planning"):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO projects (name, description, technology_stack, status) VALUES (?, ?, ?, ?)",
                (name, description, tech_stack, status)
            )
            project_id = cursor.lastrowid
            self._log_activity(cursor, project_id, "Project Created", f"Project '{name}' was created.")
            conn.commit()
            return project_id

    def update_project(self, project_id, name, description, tech_stack, status):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE projects SET name = ?, description = ?, technology_stack = ?, status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (name, description, tech_stack, status, project_id)
            )
            self._log_activity(cursor, project_id, "Project Updated", "Project details were updated.")
            conn.commit()

    def get_projects(self, search_query=""):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            if search_query:
                query = f"%{search_query}%"
                cursor.execute(
                    "SELECT * FROM projects WHERE name LIKE ? OR description LIKE ? OR technology_stack LIKE ? ORDER BY updated_at DESC",
                    (query, query, query)
                )
            else:
                cursor.execute("SELECT * FROM projects ORDER BY updated_at DESC")
            return [dict(row) for row in cursor.fetchall()]

    def get_project(self, project_id):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def delete_project(self, project_id):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM projects WHERE id = ?", (project_id,))
            conn.commit()

    # --- Tasks ---
    def get_tasks(self, project_id):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM project_tasks WHERE project_id = ?", (project_id,))
            return [dict(row) for row in cursor.fetchall()]

    def add_task(self, project_id, title, status="Pending"):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO project_tasks (project_id, title, status) VALUES (?, ?, ?)",
                (project_id, title, status)
            )
            self._log_activity(cursor, project_id, "Task Added", f"Added task: '{title}'.")
            conn.commit()
            return cursor.lastrowid

    def update_task_status(self, task_id, status):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Fetch project id for logging
            cursor.execute("SELECT project_id, title FROM project_tasks WHERE id = ?", (task_id,))
            task = cursor.fetchone()
            
            if task:
                cursor.execute("UPDATE project_tasks SET status = ? WHERE id = ?", (status, task_id))
                self._log_activity(cursor, task["project_id"], "Task Updated", f"Task '{task['title']}' marked as {status}.")
            conn.commit()

    def delete_task(self, task_id):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM project_tasks WHERE id = ?", (task_id,))
            conn.commit()

    # --- Documents ---
    def get_documents(self, project_id):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM project_documents WHERE project_id = ?", (project_id,))
            return [dict(row) for row in cursor.fetchall()]

    def save_document(self, project_id, title, content):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM project_documents WHERE project_id = ? AND title = ?", (project_id, title))
            existing = cursor.fetchone()
            if existing:
                cursor.execute(
                    "UPDATE project_documents SET content = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (content, existing["id"])
                )
                self._log_activity(cursor, project_id, "Document Updated", f"Updated document: '{title}'.")
            else:
                cursor.execute(
                    "INSERT INTO project_documents (project_id, title, content) VALUES (?, ?, ?)",
                    (project_id, title, content)
                )
                self._log_activity(cursor, project_id, "Document Added", f"Created document: '{title}'.")
            conn.commit()

    def delete_document(self, doc_id):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT project_id, title FROM project_documents WHERE id = ?", (doc_id,))
            doc = cursor.fetchone()
            if doc:
                cursor.execute("DELETE FROM project_documents WHERE id = ?", (doc_id,))
                self._log_activity(cursor, doc["project_id"], "Document Deleted", f"Deleted document: '{doc['title']}'.")
                conn.commit()

    # --- Activity Log ---
    def _log_activity(self, cursor, project_id, activity_type, description):
        cursor.execute(
            "INSERT INTO project_activities (project_id, activity_type, description) VALUES (?, ?, ?)",
            (project_id, activity_type, description)
        )

    def get_activities(self, project_id):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM project_activities WHERE project_id = ? ORDER BY created_at DESC", (project_id,))
            return [dict(row) for row in cursor.fetchall()]


class ProfileRepository(Repository):
    def get_profile(self):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM profile ORDER BY id ASC LIMIT 1")
            row = cursor.fetchone()
            if not row:
                cursor.execute("INSERT INTO profile (about) VALUES ('')")
                conn.commit()
                cursor.execute("SELECT * FROM profile ORDER BY id ASC LIMIT 1")
                row = cursor.fetchone()
            return dict(row)

    def update_profile(self, data):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE profile SET 
                about = ?, professional_goals = ?, content_preferences = ?, 
                github_preferences = ?, linkedin_preferences = ?, things_to_avoid = ?,
                updated_at = CURRENT_TIMESTAMP
                WHERE id = (SELECT id FROM profile ORDER BY id ASC LIMIT 1)
            """, (
                data.get('about', ''), data.get('professional_goals', ''),
                data.get('content_preferences', ''), data.get('github_preferences', ''),
                data.get('linkedin_preferences', ''), data.get('things_to_avoid', '')
            ))
            conn.commit()

    def get_skills(self):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM skills")
            return [dict(row) for row in cursor.fetchall()]

    def add_skill(self, name, level="Intermediate"):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("INSERT INTO skills (name, level) VALUES (?, ?)", (name, level))
                conn.commit()
            except sqlite3.IntegrityError:
                pass  # Ignore duplicate skills

    def delete_skill(self, skill_id):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM skills WHERE id = ?", (skill_id,))
            conn.commit()

    def get_achievements(self):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM achievements ORDER BY date_achieved DESC")
            return [dict(row) for row in cursor.fetchall()]

    def add_achievement(self, title, description, date_achieved, ach_type):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO achievements (title, description, date_achieved, type) VALUES (?, ?, ?, ?)",
                (title, description, date_achieved, ach_type)
            )
            conn.commit()

    def delete_achievement(self, ach_id):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM achievements WHERE id = ?", (ach_id,))
            conn.commit()

    def get_project_stats(self):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT status, COUNT(*) as count FROM projects GROUP BY status")
            return {row['status']: row['count'] for row in cursor.fetchall()}

class ProviderRepository(Repository):
    def initialize_providers(self):
        providers = ["Gemini", "Groq", "Mistral", "Cerebras"]
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            for p in providers:
                cursor.execute("INSERT OR IGNORE INTO ai_providers (name) VALUES (?)", (p,))
            conn.commit()

    def get_provider_usage_stats(self):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            # Get requests in last 24h and last 1 min, plus total tokens
            cursor.execute("""
                SELECT 
                    a.provider,
                    COUNT(a.id) as total_requests,
                    SUM(CASE WHEN a.created_at >= datetime('now', '-1 minute') THEN 1 ELSE 0 END) as req_last_min,
                    SUM(CASE WHEN a.created_at >= datetime('now', '-1 day') THEN 1 ELSE 0 END) as req_last_day
                FROM ai_events a
                GROUP BY a.provider
            """)
            events = {}
            for row in cursor.fetchall():
                d = dict(row)
                d['req_last_min'] = d.get('req_last_min') or 0
                d['req_last_day'] = d.get('req_last_day') or 0
                d['total_prompt'] = 0
                d['total_comp'] = 0
                events[d['provider']] = d
            
            cursor.execute("""
                SELECT 
                    provider, 
                    SUM(prompt_tokens) as total_prompt, 
                    SUM(completion_tokens) as total_comp 
                FROM usage_info 
                GROUP BY provider
            """)
            for row in cursor.fetchall():
                p = row['provider']
                if p not in events:
                    events[p] = {'provider': p, 'total_requests': 0, 'req_last_min': 0, 'req_last_day': 0, 'total_prompt': 0, 'total_comp': 0}
                events[p]['total_prompt'] = row['total_prompt'] or 0
                events[p]['total_comp'] = row['total_comp'] or 0
                
            return list(events.values())

    def get_model_usage_stats(self):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT p.name || ' (' || k.display_name || ')' as provider, 
                       m.model_id as model, m.name as display_name, m.rpm_limit, m.rpd_limit
                FROM models m
                JOIN ai_providers p ON m.provider_id = p.id
                JOIN api_keys_metadata k ON m.key_id = k.id
                WHERE m.is_enabled = 1
            """)
            models_dict = {}
            for row in cursor.fetchall():
                p = row['provider']
                m = row['model']
                if p not in models_dict:
                    models_dict[p] = {}
                models_dict[p][m] = {
                    "display_name": row["display_name"],
                    "req_last_min": 0,
                    "req_last_day": 0,
                    "total_requests": 0,
                    "rpm": str(row["rpm_limit"]) if row["rpm_limit"] else "API Hidden",
                    "rpd": str(row["rpd_limit"]) if row["rpd_limit"] else "API Hidden"
                }
                
            cursor.execute("""
                SELECT provider, model,
                    COUNT(id) as total_requests,
                    SUM(CASE WHEN created_at >= datetime('now', '-1 minute') THEN 1 ELSE 0 END) as req_last_min,
                    SUM(CASE WHEN created_at >= datetime('now', '-1 day') THEN 1 ELSE 0 END) as req_last_day
                FROM ai_events
                GROUP BY provider, model
            """)
            for row in cursor.fetchall():
                p_base = row['provider']
                m = row['model']
                
                # Match against all keys for this provider
                for prov_key in models_dict.keys():
                    if prov_key.startswith(f"{p_base} ("):
                        if m in models_dict[prov_key]:
                            models_dict[prov_key][m]["total_requests"] = row["total_requests"]
                            models_dict[prov_key][m]["req_last_min"] = row["req_last_min"] or 0
                            models_dict[prov_key][m]["req_last_day"] = row["req_last_day"] or 0
                    
            return models_dict

    def get_providers(self):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT p.id, p.name, p.status, 
                       k.id as key_id, k.api_key, k.last_tested, k.key_slot, k.enabled, k.display_name, k.status as key_status
                FROM ai_providers p
                LEFT JOIN api_keys_metadata k ON p.id = k.provider_id
            """)
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

                cursor.execute(f"""
                    UPDATE api_keys_metadata 
                    SET {update_key_str} status = ?, last_tested = CURRENT_TIMESTAMP, display_name = ?, enabled = ?
                    WHERE id = ?
                """, tuple(params))
            else:
                db_api_key = "••••••••" if keyring else api_key
                cursor.execute("""
                    INSERT INTO api_keys_metadata (provider_id, display_name, api_key, status, last_tested, key_slot, enabled)
                    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, ?, ?)
                """, (provider["id"], disp_name, db_api_key, status, key_slot, enabled))
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

    def save_models(self, provider_name, key_id, models_list):
        # Known good models that should default to enabled (others default to disabled)
        good_models = {
            "gemini-1.5-pro", "gemini-1.5-flash", "gemini-2.0-pro-exp", "gemini-2.5-pro", 
            "llama3-70b-8192", "llama3-8b-8192", "mixtral-8x7b-32768", "gemma2-9b-it",
            "mistral-large-latest", "mistral-small-latest", "open-mixtral-8x22b",
            "llama3.1-8b", "llama3.1-70b", "llama-3.3-70b-versatile"
        }
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM ai_providers WHERE name = ?", (provider_name,))
            provider = cursor.fetchone()
            if not provider: return
            
            p_id = provider["id"]
            
            for m in models_list:
                m_id = m["model_id"]
                # Determine default enablement
                is_enabled = 1 if any(g in m_id.lower() for g in good_models) else 0
                
                # Check if model exists for this specific key
                cursor.execute("SELECT id FROM models WHERE key_id = ? AND model_id = ?", (key_id, m_id))
                existing = cursor.fetchone()
                
                if existing:
                    cursor.execute("""
                        UPDATE models SET name=?, context_size=?, category=?, availability=?
                        WHERE id=?
                    """, (m["name"], m["context_size"], m["category"], m["availability"], existing["id"]))
                else:
                    cursor.execute("""
                        INSERT INTO models (provider_id, key_id, model_id, name, context_size, category, availability, is_enabled)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (p_id, key_id, m_id, m["name"], m["context_size"], m["category"], m["availability"], is_enabled))
            
            conn.commit()
            
    def get_models(self, key_id=None, include_disabled=False):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            base_query = """
                SELECT m.* FROM models m
            """
            
            conditions = []
            params = []
            
            if key_id:
                conditions.append("m.key_id = ?")
                params.append(key_id)
                
            if not include_disabled:
                conditions.append("m.is_enabled = 1")
                
            if conditions:
                base_query += " WHERE " + " AND ".join(conditions)
                
            cursor.execute(base_query, params)
            return [dict(row) for row in cursor.fetchall()]

    def get_available_models(self, category=None):
        """Fetches all dynamically discovered models that have valid API keys attached."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            query = """
                SELECT m.model_id, m.name, m.context_size, m.category, m.rpm_limit, m.rpd_limit,
                       p.name as provider_name, k.api_key, k.id as key_id 
                FROM models m
                JOIN api_keys_metadata k ON m.key_id = k.id
                JOIN ai_providers p ON k.provider_id = p.id
                WHERE k.enabled = 1 AND k.status NOT IN ('Invalid Key', 'Not Configured') AND m.is_enabled = 1
            """
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

class ChatRepository(Repository):
    def get_chat_history(self, project_id=None, limit=50):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            if project_id:
                cursor.execute("""
                    SELECT * FROM (
                        SELECT role, content, created_at FROM conversations 
                        WHERE project_id = ? ORDER BY created_at DESC LIMIT ?
                    ) ORDER BY created_at ASC
                """, (project_id, limit))
            else:
                cursor.execute("""
                    SELECT * FROM (
                        SELECT role, content, created_at FROM conversations 
                        WHERE project_id IS NULL ORDER BY created_at DESC LIMIT ?
                    ) ORDER BY created_at ASC
                """, (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def save_message(self, role, content, project_id=None):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO conversations (project_id, role, content)
                VALUES (?, ?, ?)
            """, (project_id, role, content))
            conn.commit()

    def clear_history(self, project_id=None):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            if project_id:
                cursor.execute("DELETE FROM conversations WHERE project_id = ?", (project_id,))
            else:
                cursor.execute("DELETE FROM conversations WHERE project_id IS NULL")
            conn.commit()

class MemoryRepository(Repository):
    def get_memories(self, category=None):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            if category:
                cursor.execute("SELECT * FROM memories WHERE category = ? ORDER BY created_at DESC, id DESC", (category,))
            else:
                cursor.execute("SELECT * FROM memories ORDER BY created_at DESC, id DESC")
            return [dict(row) for row in cursor.fetchall()]

    def search_memories(self, query):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            search_pattern = f"%{query}%"
            cursor.execute("SELECT * FROM memories WHERE content LIKE ? ORDER BY created_at DESC", (search_pattern,))
            return [dict(row) for row in cursor.fetchall()]

    def add_memory(self, category, content, importance="Medium"):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM memories WHERE content = ?", (content,))
            if not cursor.fetchone():
                cursor.execute("""
                    INSERT INTO memories (category, content, importance)
                    VALUES (?, ?, ?)
                """, (category, content, importance))
                conn.commit()

    def update_memory(self, memory_id, category, content, importance):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE memories
                SET category = ?, content = ?, importance = ?
                WHERE id = ?
            """, (category, content, importance, memory_id))
            conn.commit()

    def delete_memory(self, memory_id):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
            conn.commit()
            
    def clear_all_memories(self):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM memories")
            conn.commit()


class PostRepository(Repository):
    def get_posts(self):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM posts ORDER BY posted_at DESC")
            return [dict(row) for row in cursor.fetchall()]

    def add_post(self, platform, content):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO posts (platform, content) VALUES (?, ?)",
                (platform, content)
            )
            conn.commit()

    def delete_post(self, post_id):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM posts WHERE id = ?", (post_id,))
            conn.commit()

class CertificateRepository(Repository):
    def get_certificates(self):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM certificates ORDER BY issue_date DESC")
            return [dict(row) for row in cursor.fetchall()]

    def add_certificate(self, title, issuer, issue_date, expiry_date=None, credential_url=None):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO certificates (title, issuer, issue_date, expiry_date, credential_url) VALUES (?, ?, ?, ?, ?)",
                (title, issuer, issue_date, expiry_date, credential_url)
            )
            conn.commit()

    def delete_certificate(self, cert_id):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM certificates WHERE id = ?", (cert_id,))
            conn.commit()
            
    def update_certificate(self, cert_id, title, issuer, issue_date, expiry_date, credential_url):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE certificates SET title = ?, issuer = ?, issue_date = ?, expiry_date = ?, credential_url = ? WHERE id = ?",
                (title, issuer, issue_date, expiry_date, credential_url, cert_id)
            )
            conn.commit()

class HackathonRepository(Repository):
    def get_hackathons(self):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM hackathons ORDER BY date DESC")
            return [dict(row) for row in cursor.fetchall()]

    def add_hackathon(self, event_name, project_submitted, standing, date):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO hackathons (event_name, project_submitted, standing, date) VALUES (?, ?, ?, ?)",
                (event_name, project_submitted, standing, date)
            )
            conn.commit()

    def delete_hackathon(self, hackathon_id):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM hackathons WHERE id = ?", (hackathon_id,))
            conn.commit()
            
    def update_hackathon(self, hackathon_id, event_name, project_submitted, standing, date):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE hackathons SET event_name = ?, project_submitted = ?, standing = ?, date = ? WHERE id = ?",
                (event_name, project_submitted, standing, date, hackathon_id)
            )
            conn.commit()

