# AI-First System Design for Pivot.AI

## 🎯 Objective

Transform the system from:
- Rule-based job pipeline

Into:
- Adaptive, learning, personalized AI system

The system should:
1. Understand user + jobs semantically
2. Reason about job fit
3. Learn from user behavior
4. Proactively guide user decisions

---

## 🧠 Core Principles

### 1. Personalization
System output should differ per user based on:
- Profile
- Behavior
- Outcomes

### 2. Continuous Learning
System improves with:
- User actions (apply, ignore, save)
- Outcomes (interview, rejection)

### 3. Explainability
Every recommendation must include:
- Why it is a good fit
- Risks or gaps

### 4. Proactiveness
System should:
- Suggest actions
- Not just respond

---

## 🏗️ Architecture Overview

[Job Data Sources]
        ↓
[Ingestion Pipeline]
        ↓
[Embedding Layer]  <-- AI Layer 1
        ↓
[Scoring Engine]
        ↓
[LLM Reasoning Layer] <-- AI Layer 2
        ↓
[Pipeline State Manager]
        ↓
[Telegram Bot Delivery]

        ↑
[User Feedback Loop] <-- AI Layer 3
        ↑
[Learning System]

        ↓
[Insights Engine] <-- AI Layer 4

---

## 🧩 AI Layers Implementation

### 🔹 Layer 1: Semantic Understanding (Embeddings)

**Goal:** Replace keyword matching with semantic similarity

**Tasks:**
- Integrate embedding provider
- Generate embeddings for jobs and user profile
- Store embeddings in MongoDB
- Compute cosine similarity for scoring

---

### 🔹 Layer 2: LLM Reasoning

**Goal:** Provide intelligent explanations + decisions

**Tasks:**
- Create LLM wrapper
- Generate:
  - Fit summary
  - Risks
  - Decision (Yes/No)
  - Confidence score
- Store outputs in MongoDB

---

### 🔹 Layer 3: Learning System

**Goal:** Adapt based on user behavior

**Tasks:**
- Track user actions (apply, ignore, save)
- Track outcomes (interview, rejection)
- Adjust scoring weights dynamically

---

### 🔹 Layer 4: Insights Engine

**Goal:** Generate proactive career insights

**Tasks:**
- Aggregate historical data
- Generate insights using LLM
- Send insights via Telegram

---

## 🔁 Feedback Loop

User Action → Store → Update Model → Improve Results

---

## 📦 MongoDB Collections

### jobs
- job_id
- description
- embedding
- metadata

### users
- user_id
- profile
- embedding

### pipeline
- job_id
- user_id
- semantic_score
- llm_score
- final_score

### actions
- user_id
- job_id
- action
- outcome

### insights
- user_id
- insight
- timestamp

---

## ⚙️ APIs

- POST /user/profile
- GET /user/profile
- GET /jobs
- POST /jobs/ingest
- POST /score/job
- POST /user/action
- GET /user/insights

---

## 🗓️ Execution Plan

### Week 1
- Embeddings pipeline
- Mongo storage
- Similarity scoring

### Week 2
- LLM reasoning
- Telegram explanations

### Week 3
- Feedback tracking
- Learning heuristics

### Week 4
- Insights engine
- Proactive recommendations

---

## 🚀 Success Criteria

- Personalized job ranking
- Explainable recommendations
- Improves over time
- Provides proactive insights

---

## ❗ Anti-Patterns

- Only rule-based logic
- No feedback loop
- No personalization
- No explanations

---

## 🧠 Definition

AI-First System =
1. Understands (embeddings)
2. Reasons (LLM)
3. Learns (feedback)
4. Guides (insights)
