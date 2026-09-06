import json
import re
import logging
from app.ai.router import ModelRouter
from database.repository import MemoryRepository

logger = logging.getLogger("ForgeHub.MemoryExtractor")

class MemoryExtractor:
    def __init__(self, db_manager):
        self.router = ModelRouter(db_manager)
        self.memory_repo = MemoryRepository(db_manager)
        
    def extract_memories(self, conversation_history: list):
        if not conversation_history:
            return
            
        context_str = "\n".join([f"{msg['role'].upper()}: {msg['content']}" for msg in conversation_history])
        
        existing_memories = self.memory_repo.get_memories()
        memories_str = "Existing Memories:\n"
        for m in existing_memories:
            memories_str += f"ID: {m['id']} | Category: {m['category']} | Importance: {m['importance']} | Content: {m['content']}\n"
            
        if not existing_memories:
            memories_str += "None\n"
        
        system_prompt = f"""
        You are the Memory Extraction Core for Forge Hub.
        Your task is to analyze the recent conversation and update the user's long-term memory.
        
        {memories_str}
        
        Based on the conversation, do any existing memories need to be updated (e.g., user changed their mind)? Do any need to be deleted (e.g., no longer relevant)? What NEW facts need to be added?
        
        Return ONLY valid JSON in the following format (an array of actions):
        [
            {{"action": "ADD", "category": "Preference", "content": "User prefers concise answers", "importance": "High"}},
            {{"action": "UPDATE", "memory_id": 12, "category": "Project", "content": "Updated project scope to include UI", "importance": "Medium"}},
            {{"action": "DELETE", "memory_id": 5}}
        ]
        
        Rules:
        1. Action must be ADD, UPDATE, or DELETE.
        2. Deduplication: If a new fact is identical or semantically identical to an existing memory, do NOT ADD it. Just ignore it.
        3. Conflict: If a new fact contradicts an existing memory, output an UPDATE for that memory_id.
        4. If there is no important long-term information to extract or change, return an empty array: []
        """
        
        try:
            result, metadata = self.router.route_request(
                prompt=context_str,
                category="Lightweight", 
                system_prompt=system_prompt,
                max_tokens=1500
            )
            
            match = re.search(r'\[.*\]', result, re.DOTALL)
            if not match: return
                
            clean_resp = match.group(0).strip()
            if not clean_resp: return
                
            actions = json.loads(clean_resp)
            if not isinstance(actions, list): return
                
            for act in actions:
                if not isinstance(act, dict): continue
                
                action_type = act.get("action", "").upper()
                cat = act.get("category", "General")
                content = act.get("content", "")
                imp = act.get("importance", "Medium")
                m_id = act.get("memory_id")
                
                if action_type == "ADD" and content:
                    self.memory_repo.add_memory(cat, content, imp)
                    logger.info(f"Memory ADDED: [{cat}] {content}")
                elif action_type == "UPDATE" and m_id and content:
                    self.memory_repo.update_memory(m_id, cat, content, imp)
                    logger.info(f"Memory UPDATED (ID {m_id}): [{cat}] {content}")
                elif action_type == "DELETE" and m_id:
                    self.memory_repo.delete_memory(m_id)
                    logger.info(f"Memory DELETED (ID {m_id})")
                    
        except Exception as e:
            logger.error(f"Failed to extract/update memories: {str(e)}")

    def sync_from_profile(self):
        from database.repository import ProfileRepository, ProjectRepository, PostRepository
        prof_repo = ProfileRepository(self.memory_repo.db)
        proj_repo = ProjectRepository(self.memory_repo.db)
        post_repo = PostRepository(self.memory_repo.db)
        
        # 1. Clear old auto-synced memories
        with self.memory_repo.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM memories WHERE category = 'Profile Sync'")
            conn.commit()
            
        # 2. Gather data
        profile = prof_repo.get_profile()
        skills = [s['name'] for s in prof_repo.get_skills()]
        projects = proj_repo.get_projects()
        achievements = prof_repo.get_achievements()
        posts = post_repo.get_posts()
        linkedin = prof_repo.get_linkedin_data()
        linkedin_posts = prof_repo.get_linkedin_posts()
        github = prof_repo.get_github_data()
        
        context_str = f"""
        PROFILE AI OVERVIEW:
        {profile.get('ai_overview', 'None')}
        
        ABOUT:
        {profile.get('about', 'None')}
        
        GOALS:
        {profile.get('professional_goals', 'None')}
        
        SKILLS (General):
        {skills}
        
        PROJECTS (Internal):
        {[p['name'] + ' (' + p['status'] + '): ' + p.get('description', '') for p in projects]}
        
        ACHIEVEMENTS:
        {[a['title'] for a in achievements]}
        
        LINKEDIN PROFILE:
        - Bio: {linkedin.get('bio', '')}
        - About: {linkedin.get('about', '')}
        - Skills: {linkedin.get('skills', '')}
        - Languages: {linkedin.get('languages', '')}
        - Projects Listed: {linkedin.get('projects', '')}
        - Certificates: {linkedin.get('certificates', '')}
        - Posts: {[p['content'][:50] + ' (Media: ' + p.get('media_description', '') + ')' for p in linkedin_posts]}
        
        GITHUB PROFILE:
        - Profile README: {github.get('profile_readme', '')}
        - Projects Summary: {github.get('projects_summary', '')}
        """
        
        system_prompt = """
        You are the Profile Sync Core. Extract long-term, factual memories about the user from their profile data.
        These memories will be injected into their AI context. Focus on concrete facts (what they build, their main skills, their actual goals, their preferences).
        
        Return ONLY valid JSON in the following format (an array of actions):
        [
            {"action": "ADD", "category": "Profile Sync", "content": "User is building a React Native app", "importance": "High"},
            {"action": "ADD", "category": "Profile Sync", "content": "User's goal is to become a Staff Engineer", "importance": "High"}
        ]
        
        Rules:
        1. Action must always be "ADD" and category MUST be "Profile Sync".
        2. Keep the content extremely concise and factual.
        3. Do not include more than 30 highly important facts. Group them if necessary.
        """
        
        try:
            result, metadata = self.router.route_request(
                prompt=context_str,
                category="Reasoning", 
                system_prompt=system_prompt,
                max_tokens=2048
            )
            
            match = re.search(r'\[.*\]', result, re.DOTALL)
            if not match: return
                
            clean_resp = match.group(0).strip()
            if not clean_resp: return
                
            actions = json.loads(clean_resp)
            if not isinstance(actions, list): return
                
            for act in actions:
                if not isinstance(act, dict): continue
                if act.get("action", "").upper() == "ADD" and act.get("content"):
                    self.memory_repo.add_memory("Profile Sync", act.get("content"), act.get("importance", "Medium"))
                    
        except Exception as e:
            logger.error(f"Failed to sync profile memories: {str(e)}")
            raise e
