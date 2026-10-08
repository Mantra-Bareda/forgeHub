> **Note:** These foundational design docs were successfully implemented and have been superseded by the live V2.5 feature set in `PROJECT_STATUS.md`.

# # Product Requirements Document (PRD)

## 1. Product Overview

### Product Name
**Froge Hub**

### Product Type
Native desktop application with an AI-powered project management, professional profile management, content creation, and personal memory system.

### Product Goal

The application helps a user:

- Manage software projects and their progress.
- Maintain a professional GitHub and LinkedIn presence.
- Generate high-quality professional content.
- Decide whether something is worth posting.
- Create GitHub documentation and README files.
- Create LinkedIn posts for projects, certificates, hackathons, achievements, and other activities.
- Maintain long-term personalized memory about the user.
- Use multiple free AI providers through one unified application.
- Automatically select the best available model according to the task, model capability, context size, and provider limits.

The application should behave as a **personal professional AI manager**, not simply as a chatbot.

---

# 2. Problem Statement

Users often build projects, complete certificates, participate in hackathons, learn technologies, and achieve other things but do not maintain their professional profiles consistently.

Existing AI chat applications can generate content, but they generally do not provide a dedicated system for:

- Maintaining a long-term professional profile.
- Understanding the user's previous projects and achievements.
- Remembering the user's preferred writing style.
- Evaluating whether something should be posted.
- Maintaining consistency between GitHub and LinkedIn.
- Managing multiple free AI API providers.
- Automatically switching models when a provider reaches a limit.

This application solves these problems through a combination of:

**Project Management + Professional Profile Management + AI Content Generation + Personal Memory + AI Model Orchestration.**

---

# 3. Target Users

### Primary User

Individual developers, students, freelancers, and technical professionals who want to:

- Build a strong GitHub profile.
- Maintain a professional LinkedIn presence.
- Document their projects.
- Showcase achievements.
- Receive personalized professional advice.
- Use AI without depending on a paid single-provider API.

### Secondary Users

Anyone who wants a personal AI assistant that can maintain project and professional context over time.

---

# 4. Core Product Principles

The application should follow these principles:

### 4.1 Personalization First

The AI should understand the user's:

- Professional goals.
- Skills.
- Projects.
- Achievements.
- Writing preferences.
- Posting history.
- Professional interests.
- Previous decisions.

### 4.2 Do Not Always Agree

The AI must be allowed to recommend **not** posting something.

Example:

> "This certificate is not particularly valuable for your current profile. I recommend keeping it in your records rather than posting it."

The application should optimize for the user's **long-term professional profile**, not simply generate whatever content the user asks for.

### 4.3 Provider Independent

No feature should depend permanently on one AI provider.

The application must be able to switch between configured providers/models.

### 4.4 Local-First Configuration

The application should work without an API key during installation/startup, but AI functionality cannot be used until at least one supported API key is configured.

### 4.5 Efficient Context Usage

The application must not send the entire historical conversation or entire project history to every model request.

Only relevant information should be retrieved and supplied to the model.

---

# 5. AI Provider System

## 5.1 Supported Providers — Initial Version

The initial version will support:

1. Google Gemini
2. Groq
3. Cerebras
4. Mistral

The initial preferred model pool is:

- Gemini Flash
- Gemini Flash-Lite
- GPT-OSS-120B where available
- suitable Groq models
- suitable Cerebras models
- suitable Mistral models

The application must **not assume that a particular model is available for every API key**.

For example:

```text
User adds Gemini API key
        ↓
Application asks provider for available models
        ↓
Gemini Flash available
Gemini Flash-Lite unavailable
        ↓
Only Flash is added to the usable model pool
```

Providers expose model information differently, so the application will use provider-specific adapters behind one common internal interface. Mistral, for example, provides a model-list API that exposes model capabilities and maximum context length.

---

# 6. API Key Configuration

## First Launch

The application starts without requiring an API key to be placed in an `.env` file.

The user sees:

**Welcome → AI Provider Setup**

The user must configure at least **one API key** before using AI features.

### Maximum Keys

The initial version supports:

| Provider | Maximum Keys |
|---|---:|
| Google Gemini | 2 |
| Groq | 2 |
| Cerebras | 2 |
| Mistral | 2 |
| **Total** | **8** |

The user may configure anywhere from:

**1 → 8 API keys**

---

# 7. API Key Management

Users can:

- Add API key.
- Remove API key.
- Test API key.
- Rename/label a key.
- Enable/disable a key.
- View detected models.
- View current provider status.
- View known rate-limit state.
- Re-test unavailable keys.

API keys must be stored securely using the operating system's secure credential mechanism where possible.

API keys must never be hardcoded into the application.

---

# 8. AI Orchestration Layer

The application will contain an internal **AI Orchestration Layer / Model Router**.

Its job is to determine:

1. What the user is asking.
2. What capability is required.
3. How much context is required.
4. Which models can perform the task.
5. Which configured API keys currently have capacity.
6. Which model should be preferred.
7. Which provider should be used as fallback.
8. Whether the request should be retried.
9. Whether the request must be downgraded to a smaller model.
10. Whether the user must be informed about unavailable providers.

---

# 9. Dynamic Model Discovery

The application must not permanently hardcode:

```text
Gemini API = Gemini Flash
Groq API = GPT-OSS
```

Instead:

```text
API Key
   ↓
Provider Adapter
   ↓
Fetch available models
   ↓
Read capabilities
   ↓
Build model registry
   ↓
Classify models
```

The model registry should track information such as:

- Provider.
- API key.
- Model ID.
- Model name.
- Context window.
- Input capability.
- Output capability.
- Reasoning capability.
- Vision capability.
- Tool/function support.
- Approximate task category.
- Current availability.
- Rate-limit state.

This is necessary because available models and limits can change. Groq, for example, publishes model-specific RPM, RPD, TPM and context information and exposes remaining-limit information through response headers.

---

# 10. Model Categories

The application will internally categorize available models.

### Lightweight

For:

- Memory extraction.
- Classification.
- Simple summaries.
- Small rewrites.
- Task detection.
- Prompt/context preparation.

### General

For:

- Normal chatbot.
- General questions.
- Basic project assistance.
- Standard writing.

### Professional Writing

For:

- GitHub README.
- LinkedIn posts.
- Professional descriptions.
- Certificates.
- Hackathons.
- Project announcements.

### Reasoning

For:

- Complex project analysis.
- Professional profile decisions.
- "Should I post this?"
- Architecture reasoning.
- Difficult planning.
- Evaluating conflicting information.

### Large Context

For:

- Large project documentation.
- Long conversations.
- Multiple project files.
- Large memory retrieval.

A model can belong to multiple categories.

---

# 11. Task-Based Model Selection

The router selects models based on task requirements instead of simply using the first available API.

### Example

User:

> "Summarize this conversation."

Router:

```text
Task = Summarization
Required capability = Basic
Context = Medium
        ↓
Choose lightweight model
```

User:

> "Write a professional LinkedIn announcement for this project."

Router:

```text
Task = Professional Writing
Required quality = High
Context = Medium
        ↓
Choose best available writing model
```

User:

> "Should I post this certificate?"

Router:

```text
Task = Professional Evaluation
Required reasoning = High
Memory required = Yes
        ↓
Retrieve profile memory
        ↓
Use reasoning model
```

---

# 12. Fallback Strategy

Fallback must operate at multiple levels.

## Level 1 — Same Provider, Different Model

Example:

```text
Gemini Flash
   ↓ unavailable
Gemini Flash-Lite
```

## Level 2 — Same Model, Different API Key

Example:

```text
Groq Key 1
   ↓ rate limited
Groq Key 2
```

## Level 3 — Different Provider, Same Capability

Example:

```text
GPT-OSS-120B / Cerebras
        ↓ unavailable
GPT-OSS-120B / Groq
```

## Level 4 — Different Model, Same Task Category

Example:

```text
Best writing model
        ↓ unavailable
Second-best writing model
```

## Level 5 — Higher-capability Model

If a lightweight model is unavailable:

```text
Lightweight model
      ↓ none available
General model
      ↓ none available
High-capability model
```

The application should prefer completing the task with a stronger model rather than failing unnecessarily.

---

# 13. Rate Limit Handling

The router must track rate-limit information per provider/API key/model.

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

When a provider returns a rate-limit response such as HTTP `429`, the router should:

1. Read the retry information if provided.
2. Mark the provider/model as temporarily unavailable.
3. Try an appropriate fallback.
4. Record the event.
5. Inform the user only when necessary.

Groq explicitly returns `429 Too Many Requests` when a rate limit is exceeded and provides rate-limit/reset information through response headers.

Mistral similarly documents independent request and token limits and returns `429` when limits are exceeded.

---

# 14. Token-Aware Routing

Before sending a request, the application should estimate:

- Input tokens.
- Expected output tokens.
- Total context size.
- Model context limit.
- Provider token limits.

Example:

```text
Required context: 90K tokens

Model A:
Context = 32K
→ Reject

Model B:
Context = 128K
→ Possible

Model C:
Context = 256K
→ Preferred
```

Requests exceeding a model's context window must not be blindly sent. Mistral documents that requests exceeding a model's context window return a `400 Bad Request`.

---

# 15. Context Compiler

The application will include a **Context Compiler** between memory retrieval and the final model.

Purpose:

> Convert large amounts of stored information into a small, relevant context package.

Flow:

```text
User Request
     ↓
Task Detection
     ↓
Memory Retrieval
     ↓
Relevant Information
     ↓
Context Compiler
     ↓
Compact Context
     ↓
Selected AI Model
```

The Context Compiler should remove:

- Duplicate information.
- Irrelevant conversation history.
- Outdated information.
- Unnecessary project details.

It should preserve:

- Important user preferences.
- Relevant project information.
- Previous decisions.
- Relevant posting history.
- Current task requirements.

---

# 16. Personal Memory System

The application will maintain persistent user memory.

Memory is divided into:

### Profile Memory

Long-term information such as:

- Professional goals.
- Skills.
- Writing style.
- Content preferences.
- GitHub preferences.
- LinkedIn preferences.

### Project Memory

Information specific to a project:

- Goal.
- Technology stack.
- Architecture.
- Decisions.
- Progress.
- Problems.
- Important history.

### Achievement Memory

- Hackathons.
- Certificates.
- Awards.
- Completed projects.
- Major milestones.

### Conversation Memory

Historical conversations stored locally and searchable when relevant.

---

# 17. Memory Creation

The application should not save every message as permanent memory.

Instead:

```text
Conversation
     ↓
Memory Candidate Extraction
     ↓
Is information useful long-term?
     ↓
YES
     ↓
Create/update memory
```

The system should also detect duplicate or conflicting memories.

Example:

```text
Old:
User prefers short LinkedIn posts.

New:
User now prefers detailed technical posts.

        ↓

Update existing preference
instead of creating duplicate memory.
```

---

# 18. AI-Assisted Memory Extraction

A lightweight available model may perform memory extraction.

Example:

```text
Conversation
      ↓
Gemini Flash-Lite / suitable lightweight model
      ↓
Candidate memory
      ↓
Local validation
      ↓
Store/update memory
```

The memory system must remain functional even if the preferred lightweight model is unavailable by using the normal fallback system.

---

# 19. Professional Profile Intelligence

The application maintains a professional profile model.

It should understand:

- Current technical identity.
- Main skills.
- Strongest projects.
- Recent activities.
- GitHub quality.
- LinkedIn content pattern.
- Recent posts.
- Achievements.
- Certificates.
- Hackathons.
- Areas the user wants to improve.

The system should use this information when generating or evaluating content.

---

# 20. Professional Content Generation

The AI should support:

### GitHub

- README generation.
- README improvement.
- Project description.
- Repository description.
- Documentation structure.
- Release notes.
- Changelog content.
- Commit/PR description suggestions.
- Repository organization recommendations.
- Suggestions for screenshots/demo placement.

### LinkedIn

- Project announcements.
- Technical posts.
- Learning posts.
- Hackathon posts.
- Certificate posts.
- Achievement posts.
- Project completion posts.
- Career/professional updates.

The AI should also recommend **what visual material to attach**, such as:

- Project screenshot.
- UI screenshot.
- Architecture diagram.
- Demo GIF.
- Repository screenshot.
- Terminal output.
- Before/after comparison.

---

# 21. Professional Posting Advisor

Before generating content, the user can ask:

> "Should I post this?"

The AI evaluates:

- Professional relevance.
- Originality.
- Value to the user's profile.
- Repetition.
- Timing relative to recent posts.
- Relationship to current projects.
- Quality of the achievement.
- Whether the post makes the profile stronger or weaker.

Possible results:

### Recommended

> Strong topic. Post it.

### Recommended with changes

> Worth posting, but focus on what you built rather than the certificate itself.

### Not recommended

> I would not post this. It does not add meaningful value to your current professional profile.

---

# 22. Profile Consistency

The AI should prevent repetitive or inconsistent content.

Example:

If the user has recently posted:

```text
Certificate
Certificate
Certificate
```

and asks for another certificate post, the AI may recommend:

> Do not post another certificate right now. Your profile would benefit more from showing an actual project or technical achievement.

The application should optimize for **profile quality over content quantity**.

---

# 23. AI Response Pipeline

A typical complex request should follow:

```text
User
 ↓
Task Detector
 ↓
Determine Required Memory
 ↓
Retrieve Relevant Memory
 ↓
Context Compiler
 ↓
AI Model Router
 ↓
Select Model + API Key
 ↓
Send Request
 ↓
Validate Response
 ↓
Return Result
 ↓
Optional Memory Extraction
```

Not every request needs every step.

Simple requests should remain lightweight.

---

# 24. Simple Chat Mode

The application must also support normal chatbot behavior.

Examples:

- General questions.
- Technical questions.
- Brainstorming.
- Explanations.
- Quick rewriting.
- Project discussions.

The normal chatbot should still be able to use relevant profile/project memory when appropriate.

---

# 25. User Transparency

The application should make AI provider activity understandable.

Users should be able to see:

```text
Model:
Gemini 2.5 Flash

Provider:
Google

API:
Gemini Key 1

Reason:
Professional writing

Fallback:
GPT-OSS-120B / Cerebras
```

The application should not expose the full API key.

Example:

```text
Google Key 1
••••••••••A91F
```

---

# 26. Provider Status

The application should show provider health.

Example:

```text
Google
● Available

Groq Key 1
● Available

Groq Key 2
● Rate limited

Cerebras Key 1
● Available

Mistral Key 1
● Invalid API key
```

The user can manually test/reconnect a provider.

---

# 27. Offline Behavior

Without an API key:

- Application launches normally.
- Project management remains accessible.
- Stored profile/memory remains accessible.
- AI features display a configuration message.
- User can open Settings and add an API key.

The application should **not crash or refuse to start** because no API key exists.

---

# 28. Security Requirements

### API Keys

- Never hardcode keys.
- Never commit keys to GitHub.
- Never store plaintext keys in project files.
- Never display complete keys.
- Use OS-level secure storage where possible.

### Local Data

User project information and memories should remain local by default.

AI requests should contain only the information required for the current task.

---

# 29. Future Features

These are intentionally outside the initial version but the architecture must allow them.

### Customizable AI Harness

Future users may be able to configure:

- Preferred model.
- Preferred provider.
- Task-specific models.
- Fallback priority.
- Temperature/style.
- System prompts.
- Context rules.
- Memory rules.

This should be implemented later on top of the AI Orchestration Layer rather than replacing it.

### Additional Providers

The architecture should allow providers such as:

- Additional hosted APIs.
- Local models.
- Self-hosted inference servers.
- Other compatible APIs.

### Local AI

Future versions may support local models when the user's hardware is capable.

---

# 30. Non-Goals for Initial Version

The first version will NOT attempt to:

- Automatically post to LinkedIn.
- Automatically modify GitHub repositories without confirmation.
- Automatically publish content.
- Automatically create public profiles.
- Depend on a single AI provider.
- Include OpenRouter.
- Build a custom local foundation model.
- Provide a customizable AI harness in the first version.

The application will provide **recommendations and generated content**, while final publishing/editing remains under the user's control.

---

# 31. Success Criteria

The first version is successful if a user can:

1. Launch the application without an API key.
2. Add one or more provider API keys.
3. Automatically discover available models.
4. Use AI with only one configured provider.
5. Add additional providers later.
6. Automatically switch providers when limits/errors occur.
7. Use a smaller model for lightweight tasks.
8. Use stronger models for complex tasks.
9. Maintain persistent profile memory.
10. Maintain project-specific memory.
11. Generate professional GitHub content.
12. Generate professional LinkedIn content.
13. Ask whether something should be posted.
14. Receive personalized recommendations based on previous activity.
15. Continue using the application even when one provider becomes unavailable.

---

# 32. High-Level Product Architecture

```text
                 AI PROJECT MANAGER
                         │
        ┌────────────────┼────────────────┐
        │                │                │
   Project System   Profile System   Chat System
        │                │                │
        └────────────────┼────────────────┘
                         │
                  Memory System
                         │
                  Context Compiler
                         │
                 AI Orchestration
                         │
                  ┌──────┴──────┐
                  │ Model Router│
                  └──────┬──────┘
                         │
       ┌─────────────────┼─────────────────┐
       │                 │                 │
    Gemini             Groq            Cerebras
   Flash/Lite           ×2                ×2
       │
       └────────────────────────────────────┐
                                            │
                                         Mistral
                                       ×2 maximum
```

The architecture is designed so that **providers and models are replaceable**, while the user's project data, professional profile, memory, and application logic remain independent from them.

---

# 33. Product Vision

The final product should feel like:

> **"A personal AI project manager that knows what I am building, understands my professional profile, remembers important things about me, helps me document my work, and tells me how to present that work professionally."**

It should not feel like:

> "A chatbot with a bunch of API keys."

The AI provider system is infrastructure.

**The real product is the user's projects + professional profile + memory + personalized decision-making system.**
