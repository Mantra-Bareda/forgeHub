import logging
from app.ai.router import ModelRouter
from database.repository import ProjectRepository, ProfileRepository, CertificateRepository, HackathonRepository

logger = logging.getLogger("ForgeHub.ContentGenerator")

class PostingAdvisorResult:
    def __init__(self, recommendation, reason):
        self.recommendation = recommendation # "RECOMMENDED", "RECOMMENDED WITH CHANGES", "NOT RECOMMENDED"
        self.reason = reason

class ContentGenerator:
    def __init__(self, db_manager, compiler):
        self.db = db_manager
        self.router = ModelRouter(self.db)
        self.compiler = compiler
        
        self.proj_repo = ProjectRepository(self.db)
        self.prof_repo = ProfileRepository(self.db)
        self.cert_repo = CertificateRepository(self.db)
        self.hack_repo = HackathonRepository(self.db)

    def generate_github_readme(self, project_id: int, custom_instructions: str = "") -> str:
        project = self.proj_repo.get_project(project_id)
        if not project:
            return "Project not found."
            
        profile = self.prof_repo.get_profile()
        github_prefs = profile.get("github_preferences", "")
        
        system_prompt = (
            "You are an expert technical writer and developer advocate.\n"
            "Your task is to write a highly professional, well-structured GitHub README.md for the provided project.\n"
            f"User's GitHub Preferences: {github_prefs}\n\n"
            "Include sections like: Project Title, Description, Features, Tech Stack, Installation/Usage (if applicable)."
        )
        
        prompt = (
            f"Project Name: {project['name']}\n"
            f"Description: {project['description']}\n"
            f"Technology Stack: {project['technology_stack']}\n"
            f"Status: {project['status']}\n\n"
            f"Additional instructions: {custom_instructions}"
        )
        
        return self.router.route_request(
            prompt=prompt,
            category="Professional Writing",
            system_prompt=system_prompt,
            max_tokens=2048
        )
        
    def evaluate_posting_advisor(self, content_source: str, content_data: str) -> PostingAdvisorResult:
        system_prompt = (
            "You are the Forge Hub Professional Posting Advisor.\n"
            "Your job is to evaluate if a piece of professional news or an achievement is worth posting on LinkedIn.\n"
            "Evaluate based on: Professional Value, Originality, Relevance.\n"
            "Respond strictly in this format:\n"
            "RECOMMENDATION: [RECOMMENDED | RECOMMENDED WITH CHANGES | NOT RECOMMENDED]\n"
            "REASON: [Your detailed reasoning]"
        )
        
        profile = self.prof_repo.get_profile()
        goals = profile.get("professional_goals", "")
        
        prompt = (
            f"User Professional Goals: {goals}\n\n"
            f"Proposed Content Source: {content_source}\n"
            f"Proposed Content Details: {content_data}\n\n"
            "Analyze and provide your recommendation."
        )
        
        response = self.router.route_request(
            prompt=prompt,
            category="Reasoning",
            system_prompt=system_prompt,
            max_tokens=500
        )
        
        rec = "RECOMMENDED"
        reason = response
        
        for line in response.split('\n'):
            if line.startswith("RECOMMENDATION:"):
                raw_rec = line.replace("RECOMMENDATION:", "").strip()
                if raw_rec in ["RECOMMENDED", "RECOMMENDED WITH CHANGES", "NOT RECOMMENDED"]:
                    rec = raw_rec
            elif line.startswith("REASON:"):
                reason = line.replace("REASON:", "").strip()
                
        # Fallback if parsing failed but it gave a reason
        if reason == response:
            if "NOT RECOMMENDED" in response:
                rec = "NOT RECOMMENDED"
            elif "WITH CHANGES" in response:
                rec = "RECOMMENDED WITH CHANGES"
                
        return PostingAdvisorResult(rec, reason)

    def generate_linkedin_post(self, source_type: str, item_id: int, custom_instructions: str = "") -> str:
        data_str = ""
        
        if source_type == "Project":
            p = self.proj_repo.get_project(item_id)
            if p: data_str = f"Project '{p['name']}' using {p['technology_stack']}. Status: {p['status']}. {p['description']}"
        elif source_type == "Certificate":
            c = self.cert_repo.get_certificate(item_id)
            if c: data_str = f"Certificate '{c['title']}' from {c['issuer']}, earned {c['issue_date']}."
        elif source_type == "Hackathon":
            h = self.hack_repo.get_hackathon(item_id)
            if h: data_str = f"Hackathon '{h['event_name']}', Project: {h['project_submitted']}, Standing: {h['standing']}."
        else: # Achievement
            a = self.prof_repo.get_achievement(item_id)
            if a: data_str = f"Achievement '{a['title']}' ({a['type']}): {a['description']} on {a['date_achieved']}."
            
        if not data_str:
            return "Item not found."
            
        profile = self.prof_repo.get_profile()
        linkedin_prefs = profile.get("linkedin_preferences", "")
        avoid = profile.get("things_to_avoid", "")
        
        system_prompt = (
            "You are an expert professional brand manager and technical copywriter.\n"
            "Your task is to write a highly engaging, professional LinkedIn post for the user based on their achievement.\n"
            f"User's LinkedIn Preferences: {linkedin_prefs}\n"
            f"Things to Avoid: {avoid}\n\n"
            "Keep it authentic, not overly corporate. Use appropriate formatting and relevant hashtags."
        )
        
        prompt = (
            f"Achievement Details:\n{data_str}\n\n"
            f"Additional context/instructions: {custom_instructions}"
        )
        
        return self.router.route_request(
            prompt=prompt,
            category="Professional Writing",
            system_prompt=system_prompt,
            max_tokens=1024
        )
