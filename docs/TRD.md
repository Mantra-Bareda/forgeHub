> **Note:** These foundational design docs were successfully implemented and have been superseded by the live V2.5 feature set in `PROJECT_STATUS.md`.

# ### 1. Document Overview

**Product:** Forge Hub
**Type:** Native desktop application
**Primary Language:** Python
**GUI Framework:** PySide6 / Qt 6
**Architecture:** Modular, local-first, AI orchestration based
**Target OS:** Linux and Windows initially

---

## 2. Technical Goals

Forge Hub must:

* Manage projects and professional profile data locally.
* Connect to multiple AI providers through one unified system.
* Automatically select the best available model for each task.
* Handle API-key limits, failures and rate limits.
* Maintain persistent user/project memory.
* Avoid sending unnecessary context to AI models.
* Work even when no API key is configured.
* Remain lightweight enough for normal desktop hardware.

---

# 3. High-Level Architecture

```text
                    Forge Hub
                        │
        ┌───────────────┼────────────────┐
        │               │                │
   Project System   Profile System   Chat System
        │               │                │
        └───────────────┼────────────────┘
                        │
                  Memory System
                        │
                 Context Compiler
                        │
              AI Orchestration Layer
                        │
                  Model Router
                        │
       ┌────────┬────────┬────────┬────────┐
       │        │        │        │
    Gemini    Groq   Cerebras   Mistral
```

---

# 4. Technology Stack

| Component      | Technology                   |
| -------------- | ---------------------------- |
| Language       | Python 3.x                   |
| Desktop UI     | PySide6                      |
| UI Engine      | Qt 6                         |
| Local Database | SQLite                       |
| Configuration  | JSON / SQLite                |
| HTTP Client    | httpx                        |
| Async Tasks    | asyncio / QThread            |
| AI Integration | Provider adapters            |
| Secure Keys    | OS credential/keyring system |
| Search         | SQLite FTS5 initially        |
| Packaging      | PySide6 deployment / Nuitka  |
| Logging        | Python logging               |

---

# 5. Application Architecture

Forge Hub should use a modular architecture.

```text
forge_hub/
│
├── app/
│   ├── ui/
│   ├── core/
│   ├── projects/
│   ├── profile/
│   ├── memory/
│   ├── ai/
│   ├── storage/
│   └── security/
│
├── providers/
│   ├── gemini/
│   ├── groq/
│   ├── cerebras/
│   └── mistral/
│
├── database/
├── resources/
├── tests/
└── main.py
```

The exact structure can change during implementation, but **AI provider logic must remain separated from application/business logic.**

---

# 6. AI Provider Architecture

Forge Hub must use a common provider interface.

```text
AIProvider
 ├── GeminiProvider
 ├── GroqProvider
 ├── CerebrasProvider
 └── MistralProvider
```

Each adapter should support, where the provider allows:

* API authentication
* Model discovery
* Model information
* Request execution
* Error handling
* Rate-limit information
* Context limits
* Capability detection

Forge Hub must **not assume that every API key supports every model.**

---

# 7. API Key System

Maximum configuration:

| Provider  | Maximum Keys |
| --------- | -----------: |
| Gemini    |            2 |
| Groq      |            2 |
| Cerebras  |            2 |
| Mistral   |            2 |
| **Total** |        **8** |

Requirements:

* Keys entered inside Forge Hub.
* No `.env` requirement.
* Keys stored using OS secure storage where possible.
* Keys never shown completely after saving.
* User can:

  * Add key
  * Remove key
  * Enable/disable key
  * Rename key
  * Test key
  * View detected models
  * View current status

---

# 8. Dynamic Model Discovery

When a key is added:

```text
API Key
   ↓
Provider Adapter
   ↓
Fetch Available Models
   ↓
Detect Capabilities
   ↓
Model Registry
   ↓
Router
```

Model registry should track:

* Provider
* API key
* Model ID
* Model name
* Context window
* Input support
* Output support
* Vision support
* Tool/function calling
* Reasoning capability
* Model category
* Current availability
* Rate-limit state

This prevents Forge Hub from depending permanently on hardcoded model names.

---

# 9. Model Categories

Models can belong to multiple categories.

### Lightweight

Used for:

* Memory extraction
* Classification
* Summarization
* Task detection
* Context preparation

### General

Used for:

* Normal questions
* Basic project assistance
* Chat

### Professional Writing

Used for:

* GitHub README
* LinkedIn posts
* Certificates
* Hackathons
* Announcements
* Professional rewriting

### Reasoning

Used for:

* “Should I post this?”
* Project evaluation
* Planning
* Professional decisions

### Large Context

Used for:

* Large project documentation
* Large historical context
* Complex project analysis

---

# 10. AI Orchestration Layer

The orchestration layer is the core AI system of Forge Hub.

```text
User Request
     ↓
Task Detection
     ↓
Required Capability
     ↓
Memory Requirement
     ↓
Context Retrieval
     ↓
Context Compiler
     ↓
Model Selection
     ↓
API Request
     ↓
Validation
     ↓
Response
```

The router must select models based on:

* Task
* Capability
* Context size
* Model quality
* Token availability
* Rate limits
* Provider status
* API-key status
* Previous failures

---

# 11. Fallback System

Fallback must be **capability-based**, not simply provider-order based.

Example:

```text
Primary Model
     ↓
Same provider / another model
     ↓
Same model / another API key
     ↓
Same capability / another provider
     ↓
Another suitable model
     ↓
Stronger model
```

If a lightweight model is unavailable:

```text
Lightweight → General → Stronger Model
```

Forge Hub should not fail unnecessarily just because one preferred model is unavailable.

---

# 12. Rate-Limit Management

The system must detect and track:

* RPM
* RPD
* TPM
* TPD
* Retry time
* HTTP 429
* Provider errors

Possible states:

```text
AVAILABLE
LIMITED
TEMPORARILY_BLOCKED
DAILY_LIMIT_REACHED
INVALID_KEY
MODEL_UNAVAILABLE
PROVIDER_ERROR
```

When a rate limit occurs:

```text
429
 ↓
Read retry information
 ↓
Mark resource temporarily unavailable
 ↓
Select fallback
 ↓
Retry request
```

Provider limits should be treated as **dynamic**, not permanently hardcoded.

---

# 13. Token-Aware Routing

Before sending a request Forge Hub should estimate:

```text
Input tokens
+
Required output tokens
+
System/context tokens
=
Expected usage
```

If the selected model cannot safely handle the request, the router must select another model.

This prevents oversized prompts from reaching models that cannot support them.

---

# 14. Context Compiler

The Context Compiler reduces unnecessary AI context.

```text
User Request
     ↓
Relevant Memory
     ↓
Relevant Project Data
     ↓
Relevant Profile Data
     ↓
Remove Duplicate/Irrelevant Information
     ↓
Compact Context
     ↓
Main AI Model
```

It should preserve:

* Important user preferences
* Current project state
* Relevant decisions
* Important achievements
* Relevant previous conversations

It should remove:

* Irrelevant history
* Duplicate information
* Unnecessary conversation messages

---

# 15. Memory System

Memory will have four major layers:

```text
Profile Memory
Project Memory
Achievement Memory
Conversation Archive
```

### Profile Memory

Examples:

* Skills
* Professional goals
* Writing preferences
* LinkedIn preferences
* GitHub preferences

### Project Memory

Examples:

* Project purpose
* Technology stack
* Current status
* Decisions
* Problems
* Completed work

### Achievement Memory

Examples:

* Certificates
* Hackathons
* Awards
* Milestones

### Conversation Archive

Stores historical conversations for later retrieval.

---

# 16. Memory Processing

Forge Hub should **not save every conversation message as permanent memory.**

```text
Conversation
     ↓
Memory Candidate Extraction
     ↓
Importance Check
     ↓
Duplicate/Conflict Check
     ↓
Save / Update / Ignore
```

If a new preference conflicts with an old one, the system should update the existing memory instead of creating duplicates.

---

# 17. Professional Profile System

Profile data should include:

* Skills
* Projects
* Achievements
* Certificates
* Hackathons
* Professional goals
* GitHub activity
* LinkedIn activity
* Posting history
* Content preferences
* Things to avoid

Posting history is important for detecting repetitive content.

---

# 18. Content Generation Engine

Forge Hub should generate:

### GitHub

* README
* Project description
* Repository description
* Documentation
* Changelog
* Release notes
* PR descriptions
* Commit descriptions
* Screenshot/demo suggestions

### LinkedIn

* Project posts
* Technical posts
* Certificate posts
* Hackathon posts
* Achievement posts
* Learning updates
* Project completion posts
* Career updates

The AI should also recommend **what visual material should accompany the post.**

---

# 19. Professional Posting Advisor

The advisor evaluates:

* Professional value
* Relevance
* Originality
* Repetition
* Quality
* Profile impact
* Timing/context

Output:

```text
RECOMMENDED
RECOMMENDED WITH CHANGES
NOT RECOMMENDED
```

The system should be allowed to tell the user **not to post something**.

---

# 20. Local Storage

SQLite should store structured application data.

Possible tables:

```text
users
projects
project_tasks
profile
skills
achievements
certificates
hackathons
posts
memories
conversations
models
providers
api_keys_metadata
ai_usage
ai_events
```

Actual API keys should not be stored as normal database plaintext.

---

# 21. Security Requirements

Forge Hub must:

* Never hardcode API keys.
* Never store keys in project files.
* Avoid plaintext API-key storage.
* Mask keys in UI.
* Use OS secure credential storage where available.
* Send only required information to AI providers.
* Keep project/profile data local by default.
* Log AI events without logging API keys.
* Never expose complete keys in error messages.

---

# 22. Concurrency & UI Performance

AI requests must **never block the main Qt UI thread.**

Use:

```text
Qt UI
  ↓
Worker Thread / Async Task
  ↓
AI Request
```

The UI should remain responsive while:

* Calling APIs
* Discovering models
* Processing memory
* Searching projects
* Generating content

---

# 23. Offline Behavior

Without internet/API keys:

* Forge Hub must still launch.
* Projects remain accessible.
* Profile remains accessible.
* Memory remains accessible.
* Conversation history remains accessible.

AI features should clearly indicate that an AI provider is unavailable.

---

# 24. Logging & Diagnostics

Forge Hub should maintain local logs for:

* Application errors
* Provider failures
* Model failures
* Rate-limit events
* Fallback events
* Model selection
* Memory processing failures

Sensitive information such as API keys must never be logged.

---

# 25. Testing Requirements

Testing should cover:

### Unit Testing

* Memory operations
* Router logic
* Token estimation
* Provider adapters
* Fallback logic
* Database operations

### Integration Testing

* Provider API calls
* Model discovery
* API-key testing
* Rate-limit handling

### UI Testing

* First launch
* Settings
* Project creation
* Content generation
* Memory management

### Failure Testing

* Invalid key
* Expired/unavailable model
* 429 response
* Network failure
* Provider outage
* Oversized context

---

# 26. Packaging & Deployment

Forge Hub should be distributed as a standalone desktop application.

Target:

* **Windows:** `.exe`
* **Linux:** standalone executable/package
* **Future:** macOS

Users should not need to install Python separately to run the packaged application.

---

# 27. Future Architecture Support

The architecture should allow future addition of:

* More AI providers
* Local AI models
* Custom AI harness
* Custom routing rules
* User-selected models
* Advanced memory controls
* Additional professional platforms
* GitHub API integration
* LinkedIn integrations where officially supported

These should be added without rewriting the core orchestration system.

---

# 28. Technical Success Criteria

Forge Hub is technically successful when:

* It launches without an API key.
* At least one provider can be configured.
* Up to 8 keys can be managed.
* Models are dynamically discovered.
* Correct models are selected by task.
* Failed/rate-limited models trigger fallback.
* Large prompts are routed safely.
* Relevant memory is retrieved instead of entire history.
* Projects and profile data persist locally.
* AI requests do not freeze the UI.
* Sensitive keys are securely handled.
* The application can be packaged as a standalone desktop application.

---

## 29. Core Technical Principle

> **Forge Hub should be an application with an AI orchestration system, not an AI chatbot with an application around it.**

The AI providers are replaceable components. **Forge Hub's memory, project system, profile intelligence, routing, context compilation, and professional logic belong to Forge Hub itself.**
