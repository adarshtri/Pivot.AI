# Milestone 2: Matching, Scoring & Semantic AI

## 🎯 Objective
Enable the system to reason about the user's fit for the ingested jobs. This milestone bridges structured preferences with the first AI embedding layer to provide personalized scoring.

## 📦 Core Datasets & Database
- Introduce the **Pipeline Dataset** collection (`pipeline`) to manage job statuses and scores per user.
- Introduce embeddings to the `jobs` and `users` collections.

## ⚙️ Components to Build

### 1. Control Plane UI - Phase 2 (Preferences & Watchlist)
- **Preferences APIs**: 
  - `POST /preferences` / `GET /preferences` to manage locations (`remote`, `bay area`), company stages (`Series A/B/C`), and excluded keywords.
- **Company Watchlist API**:
  - `POST /companies` / `GET /companies` (Crucial for high-leverage company intelligence datasets).

### 2. Scoring Engine
- **v1 Rule-Based Engine**: Score jobs dynamically based on role matches, title keywords, company stage, and location alignment.

### 3. AI Layer 1: Semantic Understanding (Embeddings)
- **Integration**: Connect to an embedding provider.
- **Processing**: Generate embeddings for all incoming job descriptions and user profiles.
- **Scoring Replacement**: Augment or replace initial keyword matching with **Cosine Similarity** scoring for semantic job-to-user matching.

## 🗓️ Expected Delivery (Week 2)
- Jobs scored using both heuristic rules and vector embeddings.
- User control plane exposes toggles for remote vs location preferences and company watchlists.
- Re-scoring triggered upon User Profile or Preferences update.
