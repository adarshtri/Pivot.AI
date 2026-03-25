# Development Guide (macOS)

This guide covers setting up Pivot.AI for local development natively on a Mac (Apple Silicon or Intel).

## Prerequisites
Ensure you have the following installed on your Mac:
- **Homebrew** (`/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"`)
- **Python 3.12+** (`brew install python@3.12`)
- **Node.js 18+** (`brew install node`)
- **MongoDB** (`brew tap mongodb/brew && brew install mongodb-community@7.0`)

## 1. Start MongoDB
Pivot.AI requires MongoDB to store jobs, user profiles, and the AI pipeline. Start it locally as a background service:
```bash
brew services start mongodb-community@7.0
```

## 2. Backend Setup (FastAPI)
The core logic, ingestion engine, and AI scoring live in the Python backend.

```bash
# Clone the repository and cd into it
cd Pivot.AI

# Create and activate a virtual environment
python3.12 -m venv .venv
source .venv/bin/activate

# Install all dependencies (including fastembed + numpy for local AI scoring)
pip install -r requirements.txt

# Run the FastAPI server (runs on http://127.0.0.1:8000)
# Zero .env configuration is required; the database connection defaults to localhost.
uvicorn app.main:app --reload --port 8000
```
*Note: The first time you trigger AI Scoring from the Admin panel, the backend will download a ~67MB `all-MiniLM-L6-v2` ONNX model to your `~/.cache` directory. Subsequent runs are fully offline.*

## 3. Frontend Setup (Next.js)
The frontend is a Next.js application that proxies API requests to the FastAPI backend.

```bash
# Open a new terminal tab and navigate to the web directory
cd Pivot.AI/web

# Install required NPM packages
npm install

# Start the development server (runs on http://localhost:3000)
npm run dev
```

## 4. Bootstrapping Your Data
1. Open http://localhost:3000 in your browser.
2. Navigate to **Profile** and **Goals** inside the sidebar to configure your target roles, domains, and locations.
3. Navigate to **Admin** (Click the `user1` icon at the bottom left).
4. Click **Run Discovery** and wait for the system to identify companies matching your goals.
5. Click **Run Ingestion** to pull the global job pool from the discovered companies.
6. Click **Run AI Scoring** to process the ingested jobs through the local semantic embeddings model!

## Troubleshooting
- **Database connection refused?** Ensure MongoDB is running using `brew services list`.
- **Frontend API proxy failing?** Ensure your `web/next.config.mjs` correctly points to `http://127.0.0.1:8000`.
