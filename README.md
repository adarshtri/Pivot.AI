# Pivot.AI
**The Autonomous, AI-Native Career Intelligence Platform**

Pivot.AI is a self-driving job discovery and scoring platform designed to automate the modern job search. Instead of manually scrolling through job boards, Pivot.AI continuously scouts the web for companies matching your career goals, extracts their ATS (Applicant Tracking System) data, ingests their open roles, and uses local AI to score each job against your unique profile.

## Key Features
- **Autonomous Discovery**: Give it your target domains and roles, and Pivot.AI finds companies hiring in that space using DuckDuckGo or Brave Search.
- **Automated Ingestion**: Seamlessly scrapes open jobs directly from Greenhouse and Lever APIs.
- **AI Scoring Engine**: Runs 100% locally on your machine using `fastembed` (`all-MiniLM-L6-v2`) to calculate semantic cosine-similarity between your profile and incoming jobs, automatically punishing geographic mismatches and poorly aligned roles.
- **Kanban Pipeline**: A beautiful Next.js dark-mode interface to track your job search: Recommended, Saved, Applied, and Ignored.
- **Admin Control Plane**: Tweak ingestion intervals, discovery cycles, and trigger AI scoring manually.

## Technologies
- **Backend**: Python 3.12, FastAPI, Motor (Async MongoDB), APScheduler, FastEmbed (ONNX)
- **Frontend**: Next.js 14, React, Tailwind CSS
- **Database**: MongoDB

## Getting Started
Pivot.AI is completely free to run locally and privacy-first (AI embeddings run directly on your CPU).  
For complete, step-by-step set up instructions for macOS, see [DEVELOPMENT.md](./DEVELOPMENT.md).