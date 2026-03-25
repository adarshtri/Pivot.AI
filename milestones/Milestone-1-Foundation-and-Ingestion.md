# Milestone 1: Foundation & Data Ingestion

## 🎯 Objective
Establish the primary data pipeline and user profile integration. The goal is to build out the foundational database and set up the first layer of the control plane (User Profiles) to allow for parallel frontend/backend iteration.

## 📦 Core Datasets & Database
- Setup **MongoDB** with initial collections: `users`, `jobs`, and `companies`.
- Ensure indexes are optimized for `job_id` and `company`.

## ⚙️ Components to Build

### 1. Ingestion Service
- **Sources**: Greenhouse API, Lever API (Optional: Ashby).
- **Execution**: Set up a cron-driven fetcher.
- **Data Normalization**: Transform diverse API payloads into a common Job schema (`job_id`, `company`, `role`, `description`, `location`, `url`, `source`, `created_at`).
- **Resilience**: Implement idempotency, deduplication, retry logic, and rate limiting.

### 2. Control Plane UI - Phase 1 (Profile & Goals)
- Define a simple, form-based/CLI UI for user onboarding.
- **Profile APIs**: 
  - `POST /profile` / `GET /profile` to manage (`skills`, `experience_level`, `current_role`).
- **Goals APIs**:
  - `POST /goals` / `GET /goals` to set (`target_roles`, `domains`, `career_direction`).

## 🧱 AI & Architecture Focus
- **Parallel Development**: Ensure APIs constructed here directly inform building minimal UI components. Ensure system is highly decoupled (Interface-based design for Job Providers).
- **Multi-Tenant Prepared**: Ensure database and logic does not hard-code single-user workflows. All storage must associate data properly with a `user_id`.

## 🗓️ Expected Delivery (Week 1)
- Working FastAPI backend.
- Scripted/automated ingestion pulling actively from Greenhouse & Lever.
- Profile and Goals settings stored persistently in MongoDB for a user.
