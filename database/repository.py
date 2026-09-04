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
        import sqlite3
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

    def get_providers(self):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT p.id, p.name, p.status, k.api_key, k.last_tested 
                FROM ai_providers p
                LEFT JOIN api_keys_metadata k ON p.id = k.provider_id
            """)
            return [dict(row) for row in cursor.fetchall()]

    def save_api_key(self, provider_name, api_key, status="Valid"):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM ai_providers WHERE name = ?", (provider_name,))
            provider = cursor.fetchone()
            if not provider: return

            cursor.execute("SELECT id FROM api_keys_metadata WHERE provider_id = ?", (provider["id"],))
            existing_key = cursor.fetchone()
            
            if existing_key:
                cursor.execute("""
                    UPDATE api_keys_metadata 
                    SET api_key = ?, status = ?, last_tested = CURRENT_TIMESTAMP 
                    WHERE id = ?
                """, (api_key, status, existing_key["id"]))
            else:
                cursor.execute("""
                    INSERT INTO api_keys_metadata (provider_id, display_name, api_key, status, last_tested)
                    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (provider["id"], f"{provider_name} Default Key", api_key, status))
                
            cursor.execute("UPDATE ai_providers SET status = ? WHERE id = ?", (status, provider["id"]))
            conn.commit()

    def save_models(self, provider_name, models_list):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM ai_providers WHERE name = ?", (provider_name,))
            provider = cursor.fetchone()
            if not provider: return
            
            # Clear old models for this provider
            cursor.execute("DELETE FROM models WHERE provider_id = ?", (provider["id"],))
            
            for m in models_list:
                cursor.execute("""
                    INSERT INTO models (provider_id, model_id, name, context_size, category, availability)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (provider["id"], m["model_id"], m["name"], m["context_size"], m["category"], m["availability"]))
            
            conn.commit()
            
    def get_models(self, provider_name=None):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            if provider_name:
                cursor.execute("""
                    SELECT m.* FROM models m
                    JOIN ai_providers p ON m.provider_id = p.id
                    WHERE p.name = ?
                """, (provider_name,))
            else:
                cursor.execute("SELECT * FROM models")
            return [dict(row) for row in cursor.fetchall()]

    def get_available_models(self, category=None):
        """Fetches all dynamically discovered models that have valid API keys attached."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            query = """
                SELECT m.model_id, m.name, m.context_size, m.category, 
                       p.name as provider_name, k.api_key 
                FROM models m
                JOIN ai_providers p ON m.provider_id = p.id
                JOIN api_keys_metadata k ON p.id = k.provider_id
                WHERE k.enabled = 1 AND k.status LIKE '%Connected%'
            """
            params = []
            if category:
                query += " AND m.category = ?"
                params.append(category)
            
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

class ChatRepository(Repository):
    def get_chat_history(self, project_id=None, limit=50):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            if project_id:
                cursor.execute("""
                    SELECT role, content, created_at FROM conversations 
                    WHERE project_id = ? ORDER BY created_at ASC LIMIT ?
                """, (project_id, limit))
            else:
                cursor.execute("""
                    SELECT role, content, created_at FROM conversations 
                    WHERE project_id IS NULL ORDER BY created_at ASC LIMIT ?
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
