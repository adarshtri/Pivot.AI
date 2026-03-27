# Milestone 5: Event-Driven Architecture & Background Processing

## 🎯 Objective
Transition high-latency and heavy-compute operations to an asynchronous, event-driven model using Redis and RQ (Redis Queue). This ensures a responsive API and robust handling of long-running tasks like LLM reasoning and Telegram notifications.

## 📦 Core Datasets & Database
- **Redis**: Acts as the message broker and task storage for background workers.
- **Task Metadata**: Store task IDs and statuses in MongoDB to track progress across the system.

## ⚙️ Components to Build

### 1. Worker Infrastructure (Redis + RQ)
- **Integration**: Deploy a dedicated worker process to execute tasks off-thread.
- **Monitoring**: Integrate `rq-dashboard` to provide real-time visibility into queue health and worker performance.
- **Error Handling**: Implement standardized retry logic and dead-letter queues for failed jobs.

### 2. Global Event Gateway
- **Dispatcher**: A centralized utility to push events (e.g., `SCORE_READY`, `NOTIFY_USER`) to specific queues.
- **Prioritization**: Separate "High Priority" (System critical) from "Default" (Batch reasoning) queues.

### 3. Asynchronous AI Pipelines
- **LLM Reasoning**: Refactor the "Sieve and Scalpel" reasoning engine to run as a background task. 
- **Batch Processing**: Allow users to trigger reasoning on large sets of jobs without risk of API timeouts.

### 4. Reliable Telegram Notifications
- **Queueable Delivery**: Move all Telegram messaging operations to a persistent notification queue.
- **Rate Limit Resilience**: Automatically handle Telegram's polling/rate-limit constraints via worker retries.

## 🧱 Vision Alignment
- **Responsiveness**: The Control Plane remains lightning-fast regardless of backend compute load.
- **Reliability**: Decoupling ensures that if a service (like Telegram or an LLM Provider) is temporarily down, tasks are queued rather than lost.
- **Scalability**: Foundation for multi-worker deployments as the job pool grows.

## 🗓️ Expected Delivery (Week 5)
- Fully decoupled backend architecture with dedicated AI and Notification queues.
- Integrated monitoring dashboard for background tasks.
- Improved UI feedback for "in-progress" background operations.
