# Control Plane (UI) – Working Backwards Plan

---

## 🎯 Vision (Start from the End)

A user (you) opens Telegram and receives:

* Top 5 high-quality job opportunities
* Clear reasoning for each recommendation
* Suggestions on what to do next (apply / learn / ignore)
* Personalized insights ("You perform better with infra-heavy roles")

👉 All of this is powered by a **control plane** where the user defines:

* Who they are
* What they want
* How the system should behave

---

## 🧠 Core Principle

> The bot delivers value
> The control plane defines intelligence

---

## 🧩 Working Backwards (User Experience)

### Final Output (Bot)

User sees:

```
Top Jobs This Week:
1. AI Backend Engineer @ X (Score: 9)
   Why: Matches AI + systems + startup preference

2. ML Infra Engineer @ Y (Score: 8)
   Why: Strong infra alignment

Insights:
- You prefer backend-heavy roles
- Avoid frontend-heavy roles

Next Actions:
- Apply to 2 roles
- Learn Kubernetes (high demand)
```

---

## 🧱 What Needs to Exist Upstream

To generate this output, system needs:

1. User profile
2. Preferences & constraints
3. Goals
4. Behavior tracking
5. Scoring rules
6. Feedback loop

---

## 🖥️ Control Plane (UI) Modules

---

### 1️⃣ Profile Setup

**User sets:**

* Skills
* Experience level
* Current role

**Fields:**

```json
{
  "skills": ["backend", "distributed systems"],
  "experience_level": "L5",
  "current_role": "SDE"
}
```

**API:**

* POST /profile
* GET /profile

---

### 2️⃣ Goals Definition

**User sets:**

* Target roles
* Domains (AI, infra, etc.)
* Career direction

```json
{
  "target_roles": ["AI Engineer", "Backend Engineer"],
  "domains": ["AI", "systems"],
  "priority": "ownership"
}
```

**API:**

* POST /goals
* GET /goals

---

### 3️⃣ Preferences & Constraints

**User sets:**

* Location (remote, Bay Area)
* Company stage
* Work style

```json
{
  "locations": ["remote", "bay area"],
  "company_stage": ["Series A", "B", "C"],
  "exclude_keywords": ["frontend"]
}
```

**API:**

* POST /preferences
* GET /preferences

---

### 4️⃣ Company Watchlist

**User sets:**

* Companies to track

```json
{
  "companies": ["OpenAI", "Anthropic"]
}
```

**API:**

* POST /companies
* GET /companies

---

### 5️⃣ Feedback & Learning

**User actions:**

* Like / dislike jobs
* Mark applied / ignored

```json
{
  "job_id": "123",
  "action": "liked",
  "feedback": "good backend role"
}
```

**API:**

* POST /feedback

---

### 6️⃣ Pipeline View (Optional UI)

**User sees:**

* All tracked jobs
* Status
* Notes

**API:**

* GET /pipeline
* POST /pipeline/update

---

## 🔄 Data Flow (Control Plane → Bot)

```
User Input → Control Plane APIs → MongoDB
                                     ↓
                               Scoring Engine
                                     ↓
                                Pipeline
                                     ↓
                              Telegram Bot
```

---

## ⚙️ Backend Requirements

* Store user profile, goals, preferences
* Trigger re-scoring when inputs change
* Maintain consistency across datasets

---

## 🧪 Execution Plan

### Week 1

* Build profile + goals APIs
* Basic UI (form or CLI)

### Week 2

* Preferences + company watchlist
* Connect to scoring engine

### Week 3

* Feedback loop integration
* Pipeline APIs

### Week 4

* Telegram integration
* End-to-end flow

---

## 💡 Key Design Decisions

* Keep UI simple (form-based)
* Prioritize APIs over UI polish
* Treat control plane as source of truth
* Design for future automation (AI adjusting preferences)

---

## 🚀 Future Enhancements

* AI-generated profile suggestions
* Auto-updating goals based on behavior
* Skill gap analysis
* Resume integration

---

## 🎯 Success Criteria

* User can fully configure system via control plane
* Bot delivers personalized, relevant jobs
* System improves based on feedback

---

**End of Document**
