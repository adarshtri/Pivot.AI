# Career Pipeline System – Datasets

---

## 🎯 Objective

Define all datasets required to build a **Career Pipeline System (Pivot.AI)** that:

* Ingests job data
* Personalizes recommendations
* Tracks actions and outcomes
* Learns over time

---

## 🧠 Core Idea

> Jobs alone = noise
> Jobs + context + user data = intelligence

---

## 📊 1️⃣ Core Datasets (Must Have)

### A. Job Postings Dataset

**Sources:**

* Greenhouse
* Lever
* Ashby (optional)

```json
{
  "job_id": "string",
  "company": "string",
  "role": "string",
  "description": "string",
  "location": "string",
  "url": "string",
  "created_at": "timestamp"
}
```

**Purpose:**

* Primary input stream of opportunities

---

### B. User Profile Dataset

```json
{
  "skills": ["backend", "distributed systems", "AI"],
  "experience_level": "L5",
  "preferences": {
    "location": ["remote", "bay area"],
    "company_stage": ["Series A", "B", "C"]
  },
  "goals": ["AI systems", "ownership roles"]
}
```

**Purpose:**

* Drives personalization and scoring

---

### C. Pipeline Dataset

```json
{
  "job_id": "string",
  "score": 8,
  "status": "shortlisted",
  "notes": "strong AI infra role",
  "history": [
    {"event": "applied", "timestamp": "..."}
  ]
}
```

**Purpose:**

* Tracks lifecycle of opportunities

---

## 🚀 2️⃣ High-Leverage Datasets

### D. Company Intelligence Dataset

```json
{
  "company": "xyz",
  "stage": "Series B",
  "funding": 50000000,
  "domain": "AI infra",
  "hiring_velocity": "high"
}
```

**Sources:**

* Crunchbase
* News scraping
* Manual curation

**Purpose:**

* Helps prioritize companies

---

### E. Skills / Keywords Ontology

```json
{
  "AI": ["LLM", "transformers", "RAG"],
  "backend": ["distributed systems", "APIs"],
  "infra": ["Kubernetes", "AWS"]
}
```

**Purpose:**

* Enables better matching and scoring

---

### F. Job Embeddings Dataset (Later Stage)

```json
{
  "job_id": "123",
  "embedding": [0.123, -0.45]
}
```

**Purpose:**

* Enables semantic search and recommendations

---

## 🧩 3️⃣ Behavioral Datasets

### G. User Interaction Dataset

```json
{
  "job_id": "123",
  "action": "applied",
  "timestamp": "...",
  "feedback": "not interested in frontend-heavy roles"
}
```

**Purpose:**

* Tracks user behavior for personalization

---

### H. Outcome Dataset

```json
{
  "job_id": "123",
  "result": "interview",
  "notes": "failed system design round"
}
```

**Purpose:**

* Enables learning from results

---

## ⚙️ 4️⃣ Optional Datasets

### I. Market Trends Dataset

* Trending skills
* Hiring spikes

**Purpose:**

* Suggest what to learn next

---

### J. Resume / Portfolio Dataset

* Projects (Healthy5.AI, Pivot.AI)
* Extracted skills

**Purpose:**

* Matching resume to jobs

---

## 🔗 Data Flow

```
Jobs + Company Data + User Profile → Scoring Engine
                                      ↓
                              Pipeline Dataset
                                      ↓
                          User Actions + Outcomes
                                      ↓
                            Feedback Loop (ML later)
```

---

## 🚀 Minimal Version

### Start With:

* Jobs
* User Profile
* Pipeline

### Then Add:

* Company dataset
* Skills ontology

### Later:

* Embeddings
* Behavioral learning

---

## 💡 Key Insight

> The advantage is not collecting more data
> It’s connecting datasets meaningfully

---

## 🎯 End Goal

Build a system that answers:

* What should I apply to?
* Why?
* What should I learn next?

---

**End of Document**
