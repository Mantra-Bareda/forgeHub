import json
import time
import logging
from PySide6.QtCore import QRunnable, QObject, Signal

logger = logging.getLogger("ForgeHub.Research")

class ResearchWorkerSignals(QObject):
    finished = Signal(int, dict)
    error = Signal(str)
    needs_decision = Signal(object) # pass self
    progress = Signal(str) # To update UI on what step we're on

class RAGPipeline:
    def __init__(self):
        try:
            from duckduckgo_search import DDGS
            self.ddgs = DDGS()
        except ImportError:
            self.ddgs = None
            
    def web_search(self, query, max_results=5):
        if not self.ddgs:
            return []
        try:
            return list(self.ddgs.text(query, max_results=max_results))
        except Exception as e:
            logger.error(f"Search failed for {query}: {e}")
            return []
            
    def data_to_info(self, raw_results):
        """
        Converts a list of search result dictionaries into a structured text string
        ready for the LLM context.
        """
        if not raw_results:
            return "No data found."
            
        info_lines = []
        for r in raw_results:
            title = r.get('title', '')
            snippet = r.get('body', '')
            href = r.get('href', '')
            info_lines.append(f"Title: {title}\nSnippet: {snippet}\nSource: {href}\n")
            
        return "\n".join(info_lines)


class ResearchWorker(QRunnable):
    def __init__(self, db_manager, project_id, project_data, target_section="all"):
        super().__init__()
        self.db = db_manager
        self.project_id = project_id
        self.project_data = project_data
        self.target_section = target_section # 'all' means the new full pipeline
        self.signals = ResearchWorkerSignals()
        
        import threading
        self.decision_event = threading.Event()
        self.decision_action = "wait"
        self._is_stopped = False

    def set_decision(self, action):
        self.decision_action = action
        self.decision_event.set()
        
    def _run_ai_with_fallback(self, router, prompt, context="", category="Reasoning"):
        """Wrapper to handle rate-limiting fallback logic invisibly or prompt user."""
        from app.core.config import load_config
        cfg = load_config()
        auto_fallback = cfg.get("auto_fallback_models", False)
        
        try:
            return router.route_request(
                prompt=prompt,
                context=context,
                category=category,
                system_prompt="You are a senior technical product researcher."
            )
        except Exception as e:
            if "No available AI models" in str(e):
                raise
                
            # Rate limit trigger logic (abbreviated)
            if auto_fallback:
                return router.route_request(prompt=prompt, context=context, category="Lightweight")
            else:
                self.signals.needs_decision.emit(self)
                self.decision_event.wait()
                if self.decision_action == "use_other":
                    self.decision_event.clear()
                    return router.route_request(prompt=prompt, context=context, category="Lightweight")
                else:
                    self._is_stopped = True
                    raise Exception("Research paused due to rate limits.")

    def run(self):
        try:
            from app.ai.router import ModelRouter
            router = ModelRouter(self.db)
            rag = RAGPipeline()
            
            if not rag.ddgs:
                raise Exception("RAG dependencies (duckduckgo-search) not found. Please install them.")
            
            p_name = self.project_data.get("name", "Unknown Project")
            p_desc = self.project_data.get("description", "")
            p_feat = self.project_data.get("features", "")
            p_stack = self.project_data.get("technology_stack", "")
            
            app_context = f"App Name: {p_name}\nDesc: {p_desc}\nFeatures: {p_feat}\nStack: {p_stack}"
            
            # --- PHASE 1: GENERATE COMPETITOR QUERIES ---
            self.signals.progress.emit("Generating market search queries...")
            q1_prompt = "Analyze this app concept. Generate exactly 3 broad Google search queries to discover existing competitors, open-source alternatives, and similar tools in this specific niche. RETURN ONLY A JSON ARRAY OF STRINGS, e.g. [\"query1\", \"query2\", \"query3\"]."
            q1_response = self._run_ai_with_fallback(router, prompt=q1_prompt, context=app_context)
            if self._is_stopped: return
            
            # Parse Queries
            try:
                raw_str = q1_response[q1_response.find("["):q1_response.rfind("]")+1]
                queries_1 = json.loads(raw_str)
            except:
                queries_1 = [f"top competitors for {p_desc[:50]}", f"open source {p_name} alternative", "tools similar to " + p_name]
                
            # --- PHASE 2: EXECUTE BROAD RAG SEARCH ---
            self.signals.progress.emit("Searching for competitors across the web...")
            raw_results_1 = []
            for q in queries_1[:3]:
                time.sleep(1) # Be nice to DDG
                raw_results_1.extend(rag.web_search(q, max_results=4))
                
            info_1 = rag.data_to_info(raw_results_1)
            
            # --- PHASE 3: GENERATE DEEP QUERIES ---
            self.signals.progress.emit("Analyzing market data for deep dive...")
            q2_prompt = "Here is an app concept and some raw web data about competitors. Identify the top 2-3 competitors from the raw data. Then, generate exactly 3 highly specific Google search queries to find out their weaknesses, user complaints, and unique selling points (e.g. 'competitor_name disadvantages reddit', 'competitor_name vs'). RETURN ONLY A JSON ARRAY OF STRINGS."
            deep_context = f"App Concept:\n{app_context}\n\nBroad Market Data:\n{info_1}"
            q2_response = self._run_ai_with_fallback(router, prompt=q2_prompt, context=deep_context)
            if self._is_stopped: return
            
            try:
                raw_str = q2_response[q2_response.find("["):q2_response.rfind("]")+1]
                queries_2 = json.loads(raw_str)
            except:
                queries_2 = []
                
            # --- PHASE 4: EXECUTE DEEP RAG SEARCH ---
            self.signals.progress.emit("Deep diving into competitor advantages and flaws...")
            raw_results_2 = []
            for q in queries_2[:3]:
                time.sleep(1)
                raw_results_2.extend(rag.web_search(q, max_results=4))
                
            info_2 = rag.data_to_info(raw_results_2)
            
            # --- PHASE 5: SYNTHESIS ---
            self.signals.progress.emit("Synthesizing final actionable strategy...")
            final_prompt = """Based on the app concept and the live web research gathered, generate a final, highly actionable markdown report.
Your output MUST include:
1. **Competitors & Similar Apps**: Names and basic descriptions of the main players we found.
2. **Their USPs & Advantages**: What they do really well.
3. **Their Flaws & User Complaints**: What problems they fail to solve.
4. **Actionable Roadmap (What to build next)**: Based on the gaps in the market, give specific, strategic recommendations on what features we should build NEXT to crush the competition.
Do NOT just summarize. Tell the user EXACTLY how to win the market."""

            final_context = f"App Concept:\n{app_context}\n\nBroad Market Info:\n{info_1}\n\nDeep Competitor Info:\n{info_2}"
            
            final_report = self._run_ai_with_fallback(router, prompt=final_prompt, context=final_context, category="Reasoning")
            if self._is_stopped: return
            
            # Package it up in the new single-key format
            results_dict = {
                "actionable_research": final_report,
                # Keep publishing strategy for the other tab
                "publishing_strategy": self._run_ai_with_fallback(router, prompt="Classify this project's suitability for publishing. Is it too basic/tutorial-like, or is it unique and complex? YOU MUST OUTPUT STRICTLY A RAW JSON OBJECT with keys: 'github_suitability' (Public, Private, or Do Not Post), 'linkedin_suitability' (Recommended, Neutral, or Not Recommended), and 'reasoning' (1 sentence explaining why).", context=app_context, category="Lightweight")
            }
            
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE projects SET research_data = ? WHERE id = ?",
                    (json.dumps(results_dict), self.project_id)
                )
                conn.commit()
                
            self.signals.finished.emit(self.project_id, results_dict)

        except Exception as e:
            logger.exception("Research failed")
            self.signals.error.emit(str(e))
