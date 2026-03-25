# Milestone 3: Pipeline Management & AI Reasoning

## 🎯 Objective
Manage job applications within a tracked pipeline and integrate Large Language Models (LLMs) to provide explainable reasoning for highly-scored jobs, while learning from human feedback.

## 📦 Core Datasets & Database
- Introduce **Interaction & Outcome Datasets** (`actions` collection) tracking likes, dislikes, applied, and interview results.

## ⚙️ Components to Build

### 1. Pipeline Manager 
- **States**: `new`, `shortlisted`, `applied`, `interviewing`, `rejected`.
- **APIs**:
  - `GET /pipeline`
  - `POST /pipeline/update-status`
- Ability for users to track notes, application timestamps, and historical events.

### 2. AI Layer 2: LLM Reasoning
- **Wrapper**: Create LLM integration to generate explanations.
- **Outputs**:
  - Summarized fit (Why it's a match).
  - Risks or skills gaps.
  - Recommended Decision (Yes/No) with Confidence Score.
- Store generated insights centrally in the pipeline collection for delivery.

### 3. AI Layer 3: Learning System & Feedback Loop (Control Plane UI - Phase 3)
- **Feedback APIs**: 
  - `POST /feedback` (e.g., job disliked because "not interested in frontend-heavy roles").
- Use feedback loops to adjust rules, penalties, or scoring weights dynamically based on implicit/explicit signals (Apply vs Ignore).

## 🧱 AI & Architecture Focus
- **Explainability Principle**: No black box recommendations. Everything pushed to the pipeline must have an LLM-derived explanation of *why* it was selected.

## 🗓️ Expected Delivery (Week 3)
- Pipeline UI/system tracks ongoing jobs.
- API serves personalized explanations of fit per job.
- Logging mechanism exists for user feedback that slightly penalizes/boosts future similarity matches.
