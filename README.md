# Pivot.AI
**The Autonomous, AI-Native Career Intelligence Platform**

Pivot.AI is a self-driving job discovery and scoring platform designed to automate the modern job search. Instead of manually scrolling through job boards, Pivot.AI continuously scouts the web for companies matching your career goals, extracts their ATS (Applicant Tracking System) data, ingests their open roles, and uses advanced AI to score each opportunity against your unique profile and candidate goals.

## 🚀 Key Features

- **🌐 Autonomous Discovery & Enrichment**: 
  - Scouts hiring entities using **Brave Search** with a seamless **DuckDuckGo** fallback.
  - Automatically researches and enriches company metadata (Description, Size, Stage, Domain).
  - Unifies discovered search results with direct ingestion from Greenhouse and Lever APIs.

- **🤖 Precision AI Scoring Engine**:
  - **Personalized Verdicts**: Generates "Strong/Moderate/Weak Match" verdicts for every company and job.
  - **Multi-Goal Alignment**: Scores roles against specific candidate goals (e.g., "AI Engineering", "Remote-First").
  - **Resilient Infrastructure**: Built-in **Exponential Backoff** and rate-limiting for Groq/Ollama providers to ensure 100% uptime.

- **📄 Strategic Resume Tailoring**:
  - Generates bespoke LaTeX resumes strictly constrained to your base facts (Anti-hallucination).
  - Intelligently prioritizes experiences that match the job description and your target goals.

- **📢 Proactive Intelligence**:
  - **Multi-Bot Telegram Integration**: Get "Strong Match" alerts pushed directly to your personal Telegram bot.
  - **Command Center**: A beautiful Next.js dashboard with real-time career insights, skill gap analysis, and tactical growth recommendations.

- **🛠️ Admin Control Plane**:
  - Tweak ingestion intervals, discovery cycles, and LLM "Pulse" settings via a centralized MongoDB configuration.

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