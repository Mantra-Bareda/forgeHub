import json
import logging
from app.ai.router import ModelRouter
from database.repository import MemoryRepository

logger = logging.getLogger("ForgeHub.MemoryExtractor")

class MemoryExtractor:
    def __init__(self, db_manager):
        self.router = ModelRouter(db_manager)
        self.memory_repo = MemoryRepository(db_manager)
        
    def extract_memories(self, conversation_history: list):
        """
        Takes a list of conversation dicts [{"role": "...", "content": "..."}] 
        and extracts core facts to store in the memories database.
        """
        if not conversation_history:
            return
            
        context_str = "\n".join([f"{msg['role'].upper()}: {msg['content']}" for msg in conversation_history])
        
        system_prompt = """
        You are a memory extraction unit for Forge Hub.
        Analyze the conversation below and extract any long-term factual information about the user, their preferences, their projects, or important decisions made.
        
        Return ONLY valid JSON in the following format:
        [
            {"category": "Preference", "content": "User prefers concise answers", "importance": "High"},
            {"category": "Project", "content": "Working on a Python script for automation", "importance": "Medium"}
        ]
        
        If there is no important long-term information to extract, return an empty array: []
        """
        
        try:
            # We prefer a Lightweight model for background processing to save tokens/time
            response = self.router.route_request(
                prompt=context_str,
                category="Lightweight", 
                system_prompt=system_prompt,
                max_tokens=1024
            )
            
            # Clean response (often models return ```json ... ```)
            clean_resp = response.strip()
            if clean_resp.startswith("```json"):
                clean_resp = clean_resp[7:]
            if clean_resp.startswith("```"):
                clean_resp = clean_resp[3:]
            if clean_resp.endswith("```"):
                clean_resp = clean_resp[:-3]
                
            clean_resp = clean_resp.strip()
            
            if not clean_resp:
                return
                
            memories = json.loads(clean_resp)
            for m in memories:
                cat = m.get("category", "General")
                content = m.get("content", "")
                imp = m.get("importance", "Medium")
                if content:
                    self.memory_repo.add_memory(cat, content, imp)
                    logger.info(f"Extracted memory: [{cat}] {content}")
                    
        except Exception as e:
            logger.error(f"Failed to extract memories: {str(e)}")
