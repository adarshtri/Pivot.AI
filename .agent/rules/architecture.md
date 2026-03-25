# Pivot.AI Architecture Rules

These rules must be followed when building components for Pivot.AI:

1. **Highly Decoupled Architecture**: 
   - Never hardcode dependencies to a specific database (e.g., MongoDB), job data source, or delivery channel.
   - Use interface-based design and dependency injection to ensure modules are easily replaceable.
   - Separate the Control Plane (User UI, preferences, APIs) from the Data Plane (Job ingestion, scoring, AI processing).

2. **Product Mindset (Scalability & Multi-Tenancy)**:
   - This is NOT a single-user project. All data and logic must be multi-tenant ready.
   - Never implement hardcoded user-specific logic. 
   - All collections schema/queries must accommodate user ID partitioning.

3. **AI-First Direction**:
   - AI is the core driver of decision-making, not a bolt-on.
   - Ensure the system leverages semantic understanding (embeddings), reasoning (LLMs), learning, and proactive insights deeply within the architecture.

4. **Plug-and-Play Delivery**:
   - Treat delivery channels (Telegram, Email, Mobile) as plug-and-play modules interacting with a shared abstraction layer.
