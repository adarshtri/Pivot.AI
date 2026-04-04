# Pivot.AI
**The Autonomous, AI-Native Career Intelligence Platform**

Pivot.AI is a self-driving job discovery and scoring platform designed to automate the modern job search. Instead of manually scrolling through job boards, Pivot.AI continuously scouts the web for companies matching your career goals, extracts their ATS data, ingests their open roles, and uses advanced AI to score each opportunity against your unique profile and candidate goals.

## 🚀 Key Features

- **🌐 Autonomous Discovery & Enrichment**: 
  - Scouts hiring entities using **Brave Search** with a seamless **DuckDuckGo** fallback.
  - Automatically researches and enriches company metadata (Description, Size, Stage, Domain).
  - Unifies discovered search results with direct ingestion from Greenhouse and Lever APIs.

- **🤖 Precision AI Scoring & The "Scalpel"**:
  - **Vector scoring**: Uses **FastEmbed** with a persistent local cache for resilient, high-performance match calculations.
  - **The LLM Scalpel**: Deep-dives into your **Top 50** highest-scoring matches using **Groq (Llama-3)** to generate specific rationales, cost-optimized for high-volume pipelines.
  - **Personalized Verdicts**: Generates "Strong/Moderate/Weak Match" verdicts for every company and job.

- **📄 Strategic Resume Tailoring**:
  - Generates bespoke **LaTeX resumes** strictly constrained to your base facts (Anti-hallucination).
  - Intelligently prioritizes experiences that match the job description and your target goals.
  - Fully authenticated and user-specific, ensuring your data stays private and relevant.

- **🔐 Enterprise-Grade Identity & Multi-Tenancy**:
  - **Clerk Integration**: Seamless, secure authentication and user management.
  - **Multi-User Ready**: Built from the ground up to support multiple distinct user profiles, goals, and private pipelines.

- **📢 Proactive Intelligence**:
  - **Multi-Bot Telegram Integration**: Get "Strong Match" alerts pushed directly to your personal Telegram bot.
  - **Command Center**: A beautiful Next.js dashboard with real-time career insights and technical matching.

- **🛠️ Admin Control Plane**:
  - **Role-Based Access**: Secure admin panel controlled via Clerk metadata and database flags.
  - **System Controls**: Tweak ingestion intervals, discovery cycles, and LLM "Pulse" settings via a centralized MongoDB configuration.

## ⚡ Technologies

- **Backend**: Python 3.12, FastAPI, Motor (Async MongoDB), APScheduler, Groq/Ollama (LLM), FastEmbed (VSS)
- **Frontend**: Next.js 14, React, Tailwind CSS, Framer Motion
- **Messaging**: Telegram Bot API (Multi-tenant Webhooks)
- **Database**: MongoDB

## 🏁 Getting Started

Pivot.AI is designed to be privacy-first and highly configurable.  
For complete, step-by-step set up instructions for macOS, see [DEVELOPMENT.md](./DEVELOPMENT.md).

---
*Pivot your career with intelligence.*