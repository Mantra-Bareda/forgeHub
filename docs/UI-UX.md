> **Note:** These foundational design docs were successfully implemented and have been superseded by the live V2.5 feature set in `PROJECT_STATUS.md`.

# ````md
# UI/UX Design Document
## Forge Hub

---

## 1. Document Overview

**Product:** Forge Hub  
**Type:** Native Desktop Application  
**UI Framework:** PySide6 / Qt 6  
**Design Goal:** Simple, professional, fast, and information-focused.

Forge Hub should feel like a **professional personal workspace**, not a chatbot interface.

---

# 2. UX Principles

### 2.1 Simple
Keep the number of visible options low. Advanced controls should stay inside relevant settings.

### 2.2 Professional
The interface should look suitable for managing projects, GitHub work, achievements, and professional content.

### 2.3 Fast
Avoid unnecessary animations and heavy visual effects.

### 2.4 Context-Aware
The UI should show information relevant to the current project/task instead of overwhelming the user with everything.

### 2.5 Transparent AI
When AI is used, the user should be able to see:

- Which provider was used
- Which model was used
- Why it was selected
- Whether fallback occurred

### 2.6 User Control
The AI can recommend actions, but the user remains in control.

---

# 3. Application Layout

Main application:

```text
┌─────────────────────────────────────────────────────────────┐
│ Forge Hub                                      Profile ⚙    │
├──────────────┬──────────────────────────────────────────────┤
│              │                                              │
│ Dashboard    │                                              │
│ Projects     │              Main Content                    │
│ Profile      │                                              │
│ Content      │                                              │
│ Memory       │                                              │
│ AI Chat      │                                              │
│              │                                              │
│ ───────────  │                                              │
│ Settings     │                                              │
│ AI Providers │                                              │
│              │                                              │
├──────────────┴──────────────────────────────────────────────┤
│ AI Status: ● Ready                         Forge Hub        │
└─────────────────────────────────────────────────────────────┘
````

---

# 4. Navigation

Primary navigation:

1. **Dashboard**
2. **Projects**
3. **Profile**
4. **Content**
5. **Memory**
6. **AI Chat**

Secondary navigation:

7. **AI Providers**
8. **Settings**

Navigation should remain visible on desktop.

---

# 5. First Launch UX

Forge Hub must launch normally even with zero API keys.

### First Launch

```text
Forge Hub
Your projects. Your profile. Your AI workspace.

[ Get Started ]
```

Then:

```text
Set up AI

Forge Hub can work without AI, but AI features
require at least one provider API key.

[ Add API Key ]
[ Skip for Now ]
```

If skipped:

```text
Forge Hub is ready.

You can add an AI provider later from Settings.

[ Continue ]
```

---

# 6. Dashboard

The Dashboard is the main home screen.

### Sections

```text
Good morning

┌────────────────────┐ ┌────────────────────┐
│ Active Projects    │ │ Profile Status     │
│        5           │ │      78%            │
└────────────────────┘ └────────────────────┘

┌──────────────────────────────────────────────┐
│ Recent Projects                              │
│                                              │
│ Pixel Forge              In Progress         │
│ Forge Hub                Planning            │
│ DisasterGuard            Completed           │
└──────────────────────────────────────────────┘

┌──────────────────────────────────────────────┐
│ Professional Activity                        │
│                                              │
│ 2 projects completed                         │
│ 1 certificate added                           │
│ 3 posts this month                            │
└──────────────────────────────────────────────┘

┌──────────────────────────────────────────────┐
│ AI Suggestions                               │
│                                              │
│ Your recent project may be worth documenting.│
│                                              │
│ [ Review ]                                   │
└──────────────────────────────────────────────┘
```

The dashboard should prioritize actionable information over statistics.

---

# 7. Projects Screen

```text
Projects

[ + New Project ]                    [ Search ]

┌─────────────────────────────────────────────┐
│ Pixel Forge                                 │
│ Image → Pixel Art                            │
│ Python • Flask • Pillow                      │
│ Status: In Progress                          │
│                                             │
│ [ Open ]                                    │
└─────────────────────────────────────────────┘
```

Project cards should show:

* Project name
* Description
* Technology
* Status
* Last updated
* Optional progress

---

# 8. Project Detail Screen

```text
Pixel Forge

Overview | Tasks | Documentation | Activity | AI

Description
──────────────────────────────
...

Technology
Python • Flask • Pillow

Status
In Progress

Recent Activity
──────────────────────────────
...

AI Actions
[ Improve README ]
[ Analyze Project ]
[ Create LinkedIn Post ]
[ Ask AI ]
```

AI actions should automatically provide relevant project context.

---

# 9. Profile Screen

The Profile screen represents the user's professional identity.

```text
Professional Profile

About
──────────────────────────────
...

Skills
Python   AI   Flask   SQL   ...

Projects
5 active • 8 completed

Achievements
3

Certificates
6

Hackathons
4

Professional Preferences
──────────────────────────────
LinkedIn style: Technical
GitHub style: Detailed
Avoid: Generic motivational posts
```

The profile should be editable manually.

---

# 10. Content Screen

Central place for professional content generation.

```text
Create Content

What do you want to create?

[ GitHub README ]
[ LinkedIn Post ]
[ Certificate Post ]
[ Hackathon Post ]
[ Project Announcement ]
[ Achievement Post ]
[ Custom ]
```

After selecting:

```text
Context

Project: [ Pixel Forge ▼ ]

Purpose: [ Project Launch ▼ ]

Additional Information:
┌──────────────────────────────────────┐
│                                      │
└──────────────────────────────────────┘

[ Generate ]
```

---

# 11. Generated Content Screen

```text
Generated Content

┌────────────────────────────────────────────┐
│                                            │
│ Generated professional content             │
│                                            │
│ ...                                        │
│                                            │
└────────────────────────────────────────────┘

AI Recommendation
✓ Recommended

Why:
Strong technical value and relevant to
your existing profile.

Suggested Visuals:
• Project screenshot
• Before/after comparison
• Short demo GIF

[ Regenerate ] [ Improve ] [ Copy ]
```

The user should be able to edit generated content before using it.

---

# 12. Posting Advisor UX

This is an important Forge Hub feature.

```text
Should I Post This?

Content:
──────────────────────────────
...

Analysis

Professional Value       High
Originality               Medium
Repetition                Low
Profile Relevance         High

Recommendation

✓ RECOMMENDED

Reason:
This demonstrates a technical project that
adds something different to your recent posts.

[ Generate Post ]
```

Possible result:

```text
⚠ RECOMMENDED WITH CHANGES
```

or:

```text
✕ NOT RECOMMENDED

Reason:
This is too similar to your recent certificate
posts and adds limited new information.

Better option:
Share what you built or learned from the
experience instead.
```

---

# 13. Memory Screen

Memory should be transparent and user-controlled.

```text
Memory

[ Profile ] [ Projects ] [ Achievements ] [ Conversations ]

Important Memories

┌────────────────────────────────────────────┐
│ LinkedIn Preference                        │
│ Prefers technical/project-focused posts.   │
│                                            │
│ Importance: High                           │
│ [ Edit ] [ Delete ]                        │
└────────────────────────────────────────────┘

Recently Learned

• Prefers concise README structure
• Avoids repetitive achievement posts

[ Manage Memory ]
```

Forge Hub should never make memory feel hidden.

---

# 14. AI Chat Screen

Simple chatbot interface.

```text
AI Chat

┌────────────────────────────────────────────┐
│ You                                        │
│ Should I post my new project?              │
│                                            │
│ Forge Hub AI                               │
│ Yes, but I recommend focusing on...        │
│                                            │
│ Model: Gemini Flash                        │
│ Reason: Professional writing + profile     │
└────────────────────────────────────────────┘

┌────────────────────────────────────────────┐
│ Ask Forge Hub...                           │
└────────────────────────────────────────────┘
```

Chat should automatically use relevant project/profile memory when necessary.

---

# 15. AI Provider Screen

```text
AI Providers

Gemini
● Connected

  Key 1      ● Active
  Models: 3

  [ Test ] [ Manage ]

Groq
● Connected

  Key 1      ● Active
  Key 2      ● Available

Cerebras
○ Not configured

Mistral
○ Not configured

[ + Add Provider ]
```

---

# 16. API Key Setup

```text
Add Gemini Key

API Key
[ ••••••••••••••••••• ]

Name
[ Personal Gemini ]

[ Test Key ]

Detected Models
✓ Gemini Flash
✓ Gemini Flash-Lite

[ Save ]
```

The complete API key should never be displayed after saving.

---

# 17. AI Status Indicator

A small global status indicator should exist.

Examples:

```text
● AI Ready
```

```text
● 3 Models Available
```

```text
⚠ AI Limited
```

```text
✕ No AI Provider
```

Clicking it opens provider status.

---

# 18. AI Transparency Panel

For AI-generated responses, provide a compact expandable panel:

```text
AI Details

Provider: Gemini
Model: Gemini Flash
Task: Professional Writing
Reason: Best available writing model

Fallback: None
```

If fallback occurred:

```text
Fallback Used

Primary model unavailable.
Used: GPT-OSS-120B via Groq
```

---

# 19. Settings

Settings should contain:

### General

* Theme
* Startup behavior
* Data location

### AI Providers

* API keys
* Provider status
* Model discovery

### AI Behavior

* Preferred models
* AI response style
* Context behavior
* Memory behavior

### Memory

* Enable/disable automatic memory extraction
* Review memory
* Delete memory

### Privacy

* Local data
* AI data transmission
* Clear history

---

# 20. Empty States

Every major screen should have a useful empty state.

Example:

```text
No Projects Yet

Start by adding your first project.

[ + Create Project ]
```

AI:

```text
No AI Provider Configured

Add at least one API key to use AI features.

[ Configure AI ]
```

Memory:

```text
No Saved Memories

Forge Hub will gradually learn useful
information when memory is enabled.
```

---

# 21. Error States

Errors should explain the problem in simple language.

Bad:

```text
HTTP 429
```

Better:

```text
Gemini is temporarily rate limited.

Forge Hub will try another available model.

[ View AI Status ]
```

Invalid key:

```text
This API key could not be verified.

Check the key and try again.
```

---

# 22. Visual Design

### Style

* Clean
* Modern
* Minimal
* Professional
* Desktop-first
* Low visual noise

### Layout

* Sidebar navigation
* Cards for grouped information
* Clear headings
* Consistent spacing
* Large readable content areas

### Theme

Support:

* Light mode
* Dark mode
* System mode

Dark mode should be optimized for long development sessions.

---

# 23. Typography

Use a clean system/UI font.

Hierarchy:

```text
Page Title       24–28px
Section Title    18–20px
Body             14–16px
Secondary        12–14px
```

Avoid excessive font sizes and decorative typography.

---

# 24. Interaction Rules

* Buttons must clearly describe their action.
* Destructive actions require confirmation.
* Long AI operations show progress.
* UI must remain responsive during AI requests.
* Generated content must always be editable.
* AI suggestions must not automatically publish anything.
* Navigation should preserve unsaved work where practical.
* Keyboard shortcuts should be supported for common actions.

---

# 25. Responsive Behavior

Forge Hub is primarily a desktop application.

Minimum target layout:

```text
Width: 1000px+
```

At smaller sizes:

* Sidebar may collapse.
* Secondary panels may become tabs.
* Cards may stack vertically.
* Content editor remains the priority.

---

# 26. Accessibility

The UI should support:

* Keyboard navigation
* Visible focus states
* Readable contrast
* Tooltips for unfamiliar controls
* Scalable text where practical
* Clear status indicators without relying only on color

---

# 27. UX Priority

When deciding what appears on screen, use this priority:

```text
1. Current task
2. Relevant project/profile information
3. AI recommendation
4. Useful actions
5. Supporting information
6. Technical details
```

Technical information such as model/provider details should remain available but should not dominate the interface.

---

# 28. Core UX Flow

```text
Launch Forge Hub
       ↓
Dashboard
       ↓
Select Project / Profile / Content / Chat
       ↓
Determine Task
       ↓
Retrieve Relevant Context
       ↓
AI Processing
       ↓
Show Result
       ↓
User Reviews / Edits
       ↓
Save / Copy / Use
```

---

# 29. Design Principle

Forge Hub should feel like:

> **A professional command center for your projects, AI, and professional identity.**

It should **not** feel like:

> A chatbot with a project-management interface attached to it.

```
```
