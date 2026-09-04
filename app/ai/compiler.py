import logging
from database.repository import MemoryRepository, ProfileRepository

logger = logging.getLogger("ForgeHub.ContextCompiler")

class ContextCompiler:
    """
    Responsible for assembling the system prompt and context 
    by querying the long-term memory and user profile.
    """
    def __init__(self, db_manager):
        self.db = db_manager
        self.memory_repo = MemoryRepository(self.db)
        self.profile_repo = ProfileRepository(self.db)
        
    def compile_system_prompt(self, base_prompt: str = "") -> str:
        """
        Builds a rich system prompt that inherently "remembers" the user.
        """
        prompt_parts = []
        
        # 1. Base identity
        if not base_prompt:
            base_prompt = "You are Forge Hub, a professional AI manager designed to help the user with project management and professional tasks."
        prompt_parts.append(base_prompt)
        
        # 2. Profile integration
        try:
            profile = self.profile_repo.get_profile()
            if profile:
                profile_context = "### User Professional Profile ###\n"
                has_profile_data = False
                
                if profile.get("about"):
                    profile_context += f"About: {profile['about']}\n"
                    has_profile_data = True
                if profile.get("professional_goals"):
                    profile_context += f"Goals: {profile['professional_goals']}\n"
                    has_profile_data = True
                if profile.get("content_preferences"):
                    profile_context += f"Content Preferences: {profile['content_preferences']}\n"
                    has_profile_data = True
                if profile.get("things_to_avoid"):
                    profile_context += f"Things to Avoid: {profile['things_to_avoid']}\n"
                    has_profile_data = True
                    
                if has_profile_data:
                    prompt_parts.append(profile_context)
        except Exception as e:
            logger.error(f"Failed to load profile context: {str(e)}")
            
        # 3. Extracted Memory Points
        try:
            memories = self.memory_repo.get_memories()
            if memories:
                # Filter out low-importance memories to save tokens if we have too many, 
                # or just inject all for now.
                memory_context = "### Long-Term Memory (Extracted Facts) ###\n"
                memory_context += "Use the following facts about the user to personalize your responses.\n\n"
                
                for m in memories:
                    # e.g., "- [Preference] User prefers concise answers"
                    memory_context += f"- [{m['category']}] {m['content']}\n"
                    
                prompt_parts.append(memory_context)
        except Exception as e:
            logger.error(f"Failed to load memory context: {str(e)}")
            
        # 4. Behavioral instructions
        prompt_parts.append(
            "### Instructions ###\n"
            "1. Always adhere to the user's Content Preferences and Things to Avoid if provided.\n"
            "2. Do not hallucinate capabilities you don't have.\n"
            "3. Use the Long-Term Memory to provide personalized answers."
        )

        return "\n\n".join(prompt_parts)
