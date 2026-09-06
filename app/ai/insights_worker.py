from PySide6.QtCore import QRunnable, QObject, Signal
import logging

logger = logging.getLogger("ForgeHub.Insights")

class InsightsSignals(QObject):
    finished = Signal()
    error = Signal(str)

class BackgroundInsightsWorker(QRunnable):
    def __init__(self, db_manager, router, platform="linkedin"):
        super().__init__()
        self.db = db_manager
        self.router = router
        self.platform = platform
        self.signals = InsightsSignals()
        
    def run(self):
        try:
            from database.repository import ProfileRepository
            repo = ProfileRepository(self.db)
            
            if self.platform == "linkedin":
                data = repo.get_linkedin_data()
                context_str = f"LinkedIn Profile:\nBio: {data.get('bio')}\nAbout: {data.get('about')}\n"
                
                # Fetch related lists
                skills = [s['name'] for s in repo.get_linkedin_skills()]
                langs = [l['name'] for l in repo.get_linkedin_languages()]
                certs = [c['title'] for c in repo.get_linkedin_certificates()]
                projects = [p['title'] for p in repo.get_linkedin_projects()]
                
                context_str += f"Skills: {skills}\nLanguages: {langs}\nCertificates: {certs}\nProjects: {projects}"
                
                prompt = "Analyze this LinkedIn profile. Provide 3-4 specific, actionable suggestions on what to add, what to remove (e.g., redundant skills), or how to improve it to stand out more. Use markdown bullet points."
                
            elif self.platform == "github":
                data = repo.get_github_data()
                context_str = f"GitHub Profile:\nUsername: {data.get('username')}\nProfile README: {data.get('profile_readme')}\nProjects Summary: {data.get('projects_summary')}"
                
                prompt = "Analyze this GitHub profile. Provide 3-4 specific, actionable suggestions on what to add (e.g., more project links, tech stack details), what to remove, or how to improve the README. Use markdown bullet points."
            
            else:
                return

            # Request Insights
            result, metadata = self.router.route_request(
                prompt=prompt,
                category="Insights",
                system_prompt="You are an expert tech recruiter and profile reviewer.",
                context=context_str
            )
            
            if self.platform == "linkedin":
                repo.update_linkedin_data({"ai_insights": result})
            elif self.platform == "github":
                repo.update_github_data({"ai_insights": result})
                
            self.signals.finished.emit()
            
        except Exception as e:
            logger.error(f"Failed to generate {self.platform} insights: {e}")
            self.signals.error.emit(str(e))
