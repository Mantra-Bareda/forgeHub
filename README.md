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

**Phase 1-11 Completed & Hardened:** The foundational shell, database architecture, UI integrations, and project/profile management systems are fully functional. The backend Provider Adapter architecture is securely connected to the UI via OS Keyring storage. The intelligent `ModelRouter` layer features NLP Task Detection, routing prompts dynamically through background threads. A persistent AI memory system automatically extracts and injects core factual contexts via the `ContextCompiler`, forming a true long-term memory system.

*A massive 24-point UI-UX codebase audit has also been completed, bringing the application shell into full compliance with the core design docs. This includes fully dynamic Dashboards, tabbed Settings & Memory pages, and AI Transparency tracking in the Chat interface.*

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
