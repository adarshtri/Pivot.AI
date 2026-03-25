# Career Pipeline System – Execution Plan (Agent-Ready)

---

## 🎯 Objective

Build a **Career Pipeline System (Pivot.AI v1)** that:

* Continuously ingests job opportunities
* Filters and scores them based on user profile
* Tracks application lifecycle
* Provides actionable insights via API or Telegram bot

---

## 🏗️ High-Level Architecture

```
[ATS APIs] → [Ingestion Service] → [Database]
                                ↓
                         [Scoring Engine]
                                ↓
                         [Pipeline Manager]
                                ↓
                         [Notification Layer]
```

---

## 📦 Components

### 1. Ingestion Service

**Purpose:** Fetch job postings from external sources

**Sources:**

* Greenhouse API
* Lever API
* (Optional) Ashby / Workable

**Responsibilities:**

* Fetch jobs periodically (cron)
* Normalize data into common schema
* Deduplicate jobs

**Schema (Normalized Job Object):**

```json
{
  "job_id": "string",
  "company": "string",
  "role": "string",
  "location": "string",
  "description": "string",
  "url": "string",
  "source": "greenhouse | lever",
  "created_at": "timestamp"
}
```

**Tasks:**

* Implement API clients for Greenhouse & Lever
* Add retry + rate limiting
* Store raw + normalized data

---

### 2. Database Layer

**Recommended:** MongoDB (Document Store)

**Collections:**

#### jobs

```json
{
  "_id": "ObjectId",
  "job_id": "string",
  "company": "string",
  "role": "string",
  "description": "string",
  "location": "string",
  "url": "string",
  "source": "string",
  "created_at": "timestamp"
}
```

#### companies

```json
{
  "_id": "ObjectId",
  "name": "string",
  "domain": "string",
  "stage": "Series A | B | C",
  "priority_tag": "string"
}
```

#### pipeline

```json
{
  "_id": "ObjectId",
  "job_id": "string",
  "score": "number",
  "status": "new | shortlisted | applied | interviewing | rejected",
  "notes": "string",
  "last_updated": "timestamp"
}
```

#### user_profile

```json
{
  "_id": "ObjectId",
  "skills": ["string"],
  "preferences": {
    "locations": ["string"],
    "remote": true
  },
  "target_roles": ["string"]
}
```

**Indexes (IMPORTANT):**

* jobs.job_id (unique)
* jobs.company
* pipeline.job_id
* pipeline.status

---

### 3. Scoring Engine

**Purpose:** Rank jobs based on relevance

**Input:** job + user_profile

**Output:** score (0–10)

**Scoring Factors:**

* Role match (AI/backend/systems)
* Keywords (LLM, infra, distributed systems)
* Company stage (Series A–C preferred)
* Location preference

**Example Logic:**

```python
score = 0
if "AI" in role: score += 3
if "backend" in role: score += 2
if "LLM" in description: score += 2
if company_stage in ["A", "B", "C"]: score += 2
if location == "remote" or preferred: score += 1
```

**Tasks:**

* Implement rule-based scoring (v1)
* Store score in pipeline collection
* Design for future ML-based scoring

---

### 4. Pipeline Manager

**Purpose:** Manage lifecycle of job opportunities

**States:**

* new
* shortlisted
* applied
* interviewing
* rejected

**Responsibilities:**

* Insert new jobs into pipeline collection
* Update status based on user actions
* Track timestamps and notes

**APIs:**

* GET /pipeline
* POST /pipeline/update-status
* GET /top-jobs

---

### 5. Notification Layer

**Purpose:** Deliver actionable insights

**Channels:**

* Telegram Bot (primary)
* Optional: Email / Slack

**Features:**

* Daily/weekly top jobs
* Alerts for high-score jobs

**Example Message:**

```
Top 5 Jobs This Week:
1. Company A – AI Backend Engineer (Score: 9)
2. Company B – ML Infra Engineer (Score: 8)
```

---

## 🧠 Key Design Principles

* Keep ingestion modular
* Separate scoring from data collection
* Store everything (for future ML)
* Optimize for iteration speed

---

## ✅ Deliverables

* Working backend (FastAPI recommended)
* Database with job + pipeline data
* Telegram bot delivering top jobs
* Scoring system operational

---

## 📌 Notes for Agent

* Prioritize simplicity over completeness
* Avoid over-engineering infra
* Focus on end-to-end working system first
* Ensure idempotent ingestion (no duplicates)

---

**End of Plan**
