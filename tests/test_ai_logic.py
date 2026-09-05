import tempfile
import os
import pytest
from app.ai.compiler import ContextCompiler
from database.connection import DatabaseManager
from database.schema import initialize_database
from database.repository import MemoryRepository, ProfileRepository

@pytest.fixture
def db_manager():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    
    db = DatabaseManager(path)
    initialize_database(db)
    yield db
    
    os.remove(path)

def test_context_compiler_prioritization(db_manager):
    mem_repo = MemoryRepository(db_manager)
    # Add 20 High importance memories, 15 Medium, 10 Low
    for i in range(20): mem_repo.add_memory("HighCat", f"High {i}", "High")
    for i in range(15): mem_repo.add_memory("MedCat", f"Med {i}", "Medium")
    for i in range(10): mem_repo.add_memory("LowCat", f"Low {i}", "Low")
    
    compiler = ContextCompiler(db_manager)
    system_prompt = compiler.compile_system_prompt("Base Prompt")
    
    assert "Base Prompt" in system_prompt
    
    # 20 Highs inserted. The last 15 inserted are 5 through 19.
    assert "High 19" in system_prompt
    assert "High 5" in system_prompt
    assert "High 0" not in system_prompt
    
    # 15 Meds inserted. The last 10 inserted are 5 through 14.
    assert "Med 14" in system_prompt
    assert "Med 5" in system_prompt
    assert "Med 0" not in system_prompt
    
    # 10 Lows inserted. The last 5 inserted are 5 through 9.
    assert "Low 9" in system_prompt
    assert "Low 5" in system_prompt
    assert "Low 0" not in system_prompt

def test_context_compiler_profile_injection(db_manager):
    prof_repo = ProfileRepository(db_manager)
    
    # Initialize the row
    prof_repo.get_profile()
    
    prof_repo.update_profile({
        "about": "I am a developer",
        "professional_goals": "Build cool things",
        "content_preferences": "Short answers",
        "linkedin_preferences": "",
        "github_preferences": "",
        "things_to_avoid": "No jargon"
    })
    
    compiler = ContextCompiler(db_manager)
    prompt = compiler.compile_system_prompt()
    
    assert "I am a developer" in prompt
    assert "Build cool things" in prompt
    assert "Short answers" in prompt
    assert "No jargon" in prompt
