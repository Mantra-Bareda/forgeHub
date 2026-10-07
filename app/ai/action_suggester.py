from PySide6.QtCore import QRunnable, QObject, Signal
import logging

logger = logging.getLogger("ForgeHub.ActionSuggester")

class ActionSuggesterSignals(QObject):
    finished = Signal(str, str, str)  # old_action_id, new_label, new_prompt
    error = Signal(str)

class ActionSuggesterWorker(QRunnable):
    def __init__(self, db_manager, project_data, current_actions, completed_action_id):
        super().__init__()
        self.db = db_manager
        self.project_data = project_data
        self.current_actions = current_actions
        self.completed_action_id = completed_action_id
        self.signals = ActionSuggesterSignals()

    def run(self):
        try:
            from app.ai.router import ModelRouter
            router = ModelRouter(self.db)
            
            proj_name = self.project_data.get("name", "Project")
            proj_desc = self.project_data.get("description", "")
            
            # Identify what to replace
            current_labels = [a['label'] for a in self.current_actions]
            
            prompt = (
                f"Project '{proj_name}': {proj_desc[:200]}...\n"
                f"The user just completed an AI action. The current actions available are: {current_labels}.\n"
                "Suggest EXACTLY ONE new distinct, useful 'Quick AI Action' for this software project (e.g. 'Review Security', 'Generate Test Cases', 'Suggest Database Schema').\n"
                "Format the response EXACTLY like this on a single line:\n"
                "LABEL|PROMPT\n"
                "Example:\nGenerate Dockerfile|Write a complete, optimized Dockerfile for this project stack."
            )
            
            result, _ = router.route_request(
                prompt=prompt,
                category="General",
                system_prompt="You are a helpful AI assistant. Output ONLY the requested format 'LABEL|PROMPT'. Do not use markdown blocks.",
                max_tokens=200
            )
            
            if "|" in result:
                label, new_prompt = result.split("|", 1)
                self.signals.finished.emit(self.completed_action_id, label.strip(), new_prompt.strip())
            else:
                self.signals.error.emit("Failed to parse suggested action.")
                
        except Exception as e:
            logger.error(f"Suggester failed: {e}")
            self.signals.error.emit(str(e))
