import pytest
import os
import tempfile
from database.connection import DatabaseManager
from database.schema import initialize_database
from database.repository import ProjectRepository, ProfileRepository, MemoryRepository

@pytest.fixture
def db_manager():
    # Use a temp file for sqlite so data persists across connections
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    
    db = DatabaseManager(path)
    initialize_database(db)
    yield db
    
    # Teardown
    os.remove(path)

def test_database_initialization(db_manager):
    with db_manager.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
    assert "projects" in tables
    assert "memories" in tables
    assert "ai_providers" in tables
    assert "usage_info" in tables

def test_project_crud(db_manager):
    repo = ProjectRepository(db_manager)
    
    # Create (in the actual code it might be create_project)
    repo.create_project("Test Project", "Testing CRUD", "Python", "Planning")
    projects = repo.get_projects()
    assert len(projects) == 1
    assert projects[0]["name"] == "Test Project"
    
    # Update
    proj_id = projects[0]["id"]
    repo.update_project(proj_id, "Updated Project", "Updated Desc", "Python", "In Progress")
    updated = repo.get_project(proj_id)
    assert updated["name"] == "Updated Project"
    assert updated["status"] == "In Progress"
    
    # Delete
    repo.delete_project(proj_id)
    assert len(repo.get_projects()) == 0

def test_memory_crud_and_search(db_manager):
    repo = MemoryRepository(db_manager)
    
    # Add memories
    repo.add_memory("Preference", "User likes dark mode", "High")
    repo.add_memory("Project", "User is building an AI app", "Medium")
    
    memories = repo.get_memories()
    assert len(memories) == 2
    
    # Search
    results = repo.search_memories("dark mode")
    assert len(results) == 1
    assert results[0]["content"] == "User likes dark mode"
    
    # Update
    mem_id = results[0]["id"]
    repo.update_memory(mem_id, "Preference", "User prefers light mode now", "Low")
    updated = repo.search_memories("light mode")
    assert len(updated) == 1
    assert updated[0]["importance"] == "Low"
