SCHEMA = """
-- Projects
CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    technology_stack TEXT,
    status TEXT DEFAULT 'Planning',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS project_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    status TEXT DEFAULT 'Pending',
    FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS project_activities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    activity_type TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS project_documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    content TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
);

-- Profile & Achievements
CREATE TABLE IF NOT EXISTS profile (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    about TEXT,
    professional_goals TEXT,
    content_preferences TEXT,
    github_preferences TEXT,
    linkedin_preferences TEXT,
    things_to_avoid TEXT,
    ai_overview TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS skills (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    level TEXT
);

CREATE TABLE IF NOT EXISTS achievements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    date_achieved DATE,
    type TEXT -- 'Certificate', 'Hackathon', 'Award', 'General'
);

CREATE TABLE IF NOT EXISTS posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    platform TEXT,
    content TEXT NOT NULL,
    posted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Memory & AI
CREATE TABLE IF NOT EXISTS memories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT,
    content TEXT NOT NULL,
    importance TEXT DEFAULT 'Medium',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER,
    chat_context TEXT DEFAULT 'general',
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
);

-- Providers
CREATE TABLE IF NOT EXISTS ai_providers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    status TEXT DEFAULT 'Not Configured'
);

CREATE TABLE IF NOT EXISTS api_keys_metadata (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    provider_id INTEGER NOT NULL,
    display_name TEXT NOT NULL,
    api_key TEXT,
    enabled BOOLEAN DEFAULT 1,
    status TEXT,
    last_tested TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(provider_id) REFERENCES ai_providers(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS models (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    provider_id INTEGER NOT NULL,
    key_id INTEGER,
    model_id TEXT NOT NULL,
    name TEXT,
    context_size INTEGER,
    category TEXT,
    availability TEXT,
    vision BOOLEAN DEFAULT 0,
    reasoning BOOLEAN DEFAULT 0,
    tool_support BOOLEAN DEFAULT 0,
    is_enabled INTEGER DEFAULT 1,
    rpm_limit INTEGER DEFAULT NULL,
    rpd_limit INTEGER DEFAULT NULL,
    input_capability TEXT,
    output_capability TEXT,
    last_checked TIMESTAMP,
    FOREIGN KEY(provider_id) REFERENCES ai_providers(id) ON DELETE CASCADE
);

-- Certificates
CREATE TABLE IF NOT EXISTS certificates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    issuer TEXT,
    issue_date DATE,
    expiry_date DATE,
    credential_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Hackathons
CREATE TABLE IF NOT EXISTS hackathons (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_name TEXT NOT NULL,
    project_submitted TEXT,
    standing TEXT,
    date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- AI Events Tracking
CREATE TABLE IF NOT EXISTS ai_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    provider TEXT,
    model TEXT,
    task_type TEXT,
    status TEXT,
    latency_ms INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Usage Tracking
CREATE TABLE IF NOT EXISTS usage_info (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    provider TEXT,
    model TEXT,
    prompt_tokens INTEGER DEFAULT 0,
    completion_tokens INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- LinkedIn Data
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
);

CREATE TABLE IF NOT EXISTS linkedin_posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content TEXT NOT NULL,
    media_description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS linkedin_certificates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS linkedin_projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS linkedin_skills (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS linkedin_languages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

-- GitHub Data
CREATE TABLE IF NOT EXISTS github_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    profile_readme TEXT,
    projects_summary TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

def initialize_database(db_manager):
    with db_manager.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA user_version")
        version = cursor.fetchone()[0]
        
        if version == 0:
            conn.executescript(SCHEMA)
            cursor.execute("PRAGMA user_version = 1")
        elif version == 1:
            pass # Add future migrations here
            
        conn.commit()
