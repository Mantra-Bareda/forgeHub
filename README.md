# Forge Hub

Forge Hub is a native desktop application designed as a **personal professional AI manager**. It goes beyond standard chatbots to provide an AI-powered project management, professional profile tracking, content creation, and personalized memory system.

## 🚀 Key Features (In Development)

- **Project Management**: Track active projects, manage tasks, and maintain repository documentation entirely locally.
- **Professional Profile**: Curate your technical skills, hackathons, certificates, and achievements in one centralized view.
- **AI Content Orchestration**: Seamlessly integrate with multiple AI providers (Gemini, Groq, Cerebras, Mistral) through dynamic model discovery and smart, task-based routing.
- **Professional Posting Advisor**: AI evaluates whether an accomplishment improves your professional profile and suggests how to announce it on LinkedIn or GitHub.
- **Long-Term Memory**: The system builds an ongoing understanding of your writing style, preferences, and project history without redundantly sending your entire chat history to APIs.

## 🛠 Technology Stack

- **Language**: Python 3.10+
- **GUI Framework**: PySide6 (Qt 6)
- **Local Storage**: SQLite
- **Architecture**: Modular, local-first, independent AI orchestration

## 📈 Current Progress

**Phase 1-10 Completed:** The foundational shell, database architecture, UI integrations, and project/profile management systems are fully functional. The backend Provider Adapter architecture is seamlessly connected to the UI. The intelligent `ModelRouter` layer routes prompts dynamically through background threads while logging conversations. A persistent AI memory system automatically analyzes conversations, extracts core factual contexts into JSON, and saves them locally, forming a true long-term memory compiler.

## 💻 Getting Started

Forge Hub runs locally and does **not** require API keys to function as a project manager, although adding API keys in the Settings unlocks its AI orchestration capabilities.

### Installation

1. Clone the repository
2. Set up a virtual environment: `python3 -m venv venv`
3. Activate the environment: `source venv/bin/activate` (Linux/Mac) or `venv\Scripts\activate` (Windows)
4. Install dependencies: `pip install PySide6`
5. Run the application: `python main.py`

## 🛡 Security & Privacy
All project data, professional profiles, and memory logs are stored **locally** on your device using SQLite. API Keys are managed securely and never hard-coded or logged. Only relevant, compiled context is sent to AI Providers during generation.
