# Forge Hub — Application Flow Document

## 1. Overall Application Flow

```text
Launch Forge Hub
        │
        ▼
Welcome / First Launch
        │
        ├── API Key Setup
        │       ├── Add Provider
        │       ├── Test Key
        │       └── Detect Models
        │
        └── Skip for Now
                │
                ▼
           Dashboard
                │
      ┌─────────┼──────────┐
      ▼         ▼          ▼
  Projects   Profile    Content
      │         │          │
      └─────────┼──────────┘
                ▼
             AI Chat
                │
                ▼
        AI Orchestration
                │
       ┌────────┼────────┐
       ▼        ▼        ▼
    Memory   Context    Router
             Compiler
                │
                ▼
          Selected Model
                │
                ▼
             Result
```

---

# 2. First Launch Flow

```text
Launch
  ↓
Forge Hub Welcome
  ↓
Get Started
  ↓
AI Setup
  │
  ├── Add API Key
  │      ↓
  │   Select Provider
  │      ↓
  │   Enter Key
  │      ↓
  │   Test Key
  │      ↓
  │   Discover Models
  │      ↓
  │   Save
  │
  └── Skip
         ↓
      Dashboard
```

**Rule:** Forge Hub must launch and remain usable even with zero API keys.

---

# 3. Dashboard Flow

```text
Dashboard
   │
   ├── Recent Projects
   │       ↓
   │    Project Details
   │
   ├── Professional Activity
   │       ↓
   │    Content / Profile
   │
   ├── AI Suggestions
   │       ↓
   │    Review Recommendation
   │
   └── AI Status
           ↓
       Provider Status
```

Dashboard is the central starting point, not the place for detailed editing.

---

# 4. Project Flow

```text
Projects
   ↓
New Project
   ↓
Project Information
   ↓
Create
   ↓
Project Dashboard
   │
   ├── Overview
   ├── Tasks
   ├── Documentation
   ├── Activity
   └── AI
          │
          ├── Analyze Project
          ├── Improve README
          ├── Create LinkedIn Post
          └── Ask AI
```

---

# 5. Project Creation Flow

```text
+ New Project
      ↓
Project Name
      ↓
Description
      ↓
Technology / Stack
      ↓
Status
      ↓
Optional Files / Documentation
      ↓
Create Project
      ↓
Project Memory Created
      ↓
Project Dashboard
```

---

# 6. Professional Profile Flow

```text
Profile
   ↓
Profile Overview
   │
   ├── About
   ├── Skills
   ├── Projects
   ├── Achievements
   ├── Certificates
   ├── Hackathons
   └── Professional Preferences
```

Any profile change should update the relevant profile memory.

---

# 7. Content Generation Flow

```text
Content
   ↓
Choose Content Type
   │
   ├── GitHub README
   ├── LinkedIn Post
   ├── Certificate
   ├── Hackathon
   ├── Achievement
   ├── Project Announcement
   └── Custom
        ↓
Select Context
        ↓
Project / Achievement / Profile
        ↓
Additional Information
        ↓
Generate
        ↓
AI Processing
        ↓
Generated Content
        ↓
Review / Edit
        ↓
Copy / Save
```

Forge Hub must **not automatically publish** the generated content.

---

# 8. LinkedIn Post Flow

```text
Create Content
      ↓
LinkedIn Post
      ↓
Select Source
      │
      ├── Project
      ├── Certificate
      ├── Hackathon
      ├── Achievement
      └── Custom
      ↓
Retrieve Relevant Profile Memory
      ↓
Check Previous Posts
      ↓
Generate Post
      ↓
Suggest Visuals
      ↓
Show Recommendation
      ↓
Edit
      ↓
Copy / Save
```

Previous posts are checked to reduce repetitive content.

---

# 9. "Should I Post This?" Flow

```text
Posting Advisor
      ↓
Enter / Select Content
      ↓
Retrieve Profile + Posting History
      ↓
AI Analysis
      ↓
Evaluate:
  • Professional Value
  • Relevance
  • Originality
  • Repetition
  • Profile Impact
      ↓
Recommendation
      │
      ├── Recommended
      ├── Recommended With Changes
      └── Not Recommended
```

If **Not Recommended**, Forge Hub should explain why and suggest a better direction when possible.

---

# 10. Memory Flow

```text
Conversation / Project Activity
            ↓
     Memory Candidate
            ↓
     Importance Check
            ↓
    Duplicate / Conflict Check
            ↓
       ┌────┴────┐
       ▼         ▼
     Save      Ignore
       │
       ▼
   Memory Store
```

Memory can also be manually edited or deleted.

---

# 11. AI Chat Flow

```text
AI Chat
   ↓
User Request
   ↓
Task Detection
   ↓
Does Context Matter?
   │
   ├── No ──────────────┐
   │                    │
   └── Yes              │
        ↓               │
   Retrieve Relevant    │
   Memory/Project       │
        ↓               │
   Context Compiler     │
        │               │
        └───────┬───────┘
                ▼
          Model Router
                ↓
         Select Model + Key
                ↓
            AI Request
                ↓
             Response
                ↓
        Optional Memory Update
```

---

# 12. AI Provider Setup Flow

```text
AI Providers
     ↓
Add Provider
     ↓
Select:
Gemini / Groq / Cerebras / Mistral
     ↓
Enter API Key
     ↓
Test
     ↓
Fetch Available Models
     ↓
Detect Capabilities
     ↓
Save Provider
     ↓
Available in Router
```

---

# 13. Model Failure Flow

```text
AI Request
    ↓
Selected Model
    ↓
Request Failed?
    │
    ├── No → Response
    │
    └── Yes
         ↓
      Determine Error
         ↓
      Update Status
         ↓
      Find Fallback
         ↓
      Retry
         │
         ├── Success → Response
         │
         └── Failure → Next Fallback
```

The user should only see technical fallback details when useful.

---

# 14. Settings Flow

```text
Settings
   │
   ├── General
   ├── AI Providers
   │      ↓
   │   Keys / Models / Status
   │
   ├── AI Behavior
   │
   ├── Memory
   │
   └── Privacy
```

---

# 15. Navigation Flow

```text
                    Dashboard
                 /      |      \
                /       |       \
          Projects    Profile   Content
             │          │          │
             │          │          │
             └──────────┼──────────┘
                        │
                     AI Chat
                        │
                  ┌─────┴─────┐
                  │           │
               Memory      AI System
                              │
                    ┌─────────┼─────────┐
                    ▼         ▼         ▼
                 Context    Router   Providers
```

---

# 16. Global AI Processing Flow

Every AI-powered feature follows the same basic pipeline:

```text
User Action
    ↓
Task Detection
    ↓
Context Requirement
    ↓
Memory Retrieval
    ↓
Context Compiler
    ↓
Model Selection
    ↓
Token / Limit Check
    ↓
AI Request
    ↓
Validation
    ↓
Response
    ↓
Optional Memory Extraction
```

---

# 17. Offline Flow

```text
Launch
  ↓
No Internet / No API Key
  ↓
Dashboard
  │
  ├── Projects → Available
  ├── Profile → Available
  ├── Memory → Available
  ├── History → Available
  │
  └── AI Feature
          ↓
     AI Unavailable
          ↓
     Configure Provider
```

---

# 18. Complete User Journey

### New User

```text
Launch
 ↓
Welcome
 ↓
Add API Key / Skip
 ↓
Dashboard
 ↓
Create Project
 ↓
Work on Project
 ↓
Update Project
 ↓
AI Analyze Project
 ↓
Generate README
 ↓
Complete Project
 ↓
Posting Advisor
 ↓
Generate LinkedIn Post
 ↓
Save Post
 ↓
Profile Updated
 ↓
Memory Updated
```

### Returning User

```text
Launch
 ↓
Dashboard
 ↓
Relevant Project / Activity
 ↓
AI Suggestion
 ↓
Review
 ↓
AI Assistance
 ↓
Save Result
```

---

# 19. Core Navigation Rule

At any point, the user should be able to reach:

* Dashboard
* Projects
* Profile
* Content
* Memory
* AI Chat
* AI Providers
* Settings

without losing the current application state unnecessarily.

---

# 20. Final UX Principle

```text
User
 ↓
Forge Hub understands the context
 ↓
Forge Hub retrieves only what matters
 ↓
Forge Hub selects the right AI
 ↓
Forge Hub gives useful advice/result
 ↓
User decides what to do
```

**Forge Hub assists, recommends, and manages context — but the user remains the final decision-maker.**
