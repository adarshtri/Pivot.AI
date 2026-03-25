# Pivot.AI Development Workflow Rules

These rules dictate how you should iteratively develop Pivot.AI:

1. **User-First System & Simplicity**:
   - Prioritize ease of use and accessibility. Avoid exposing developer-first workflows or overly complex UX to users.
   - Build simple onboarding flows and intuitive UI components over technically complex dashboards.

2. **Parallel Frontend & Backend Development**:
   - Do NOT build out the backend sequentially before the frontend.
   - Frontend and backend must be built in parallel.
   - When creating a new API, immediately build minimal UI alongside it to validate the flow end-to-end.

3. **Validation over Polish**:
   - Do not over-engineer features before user validation.
   - Optimize for fast iteration cycles and immediate feedback over heavy upfront planning of edge cases.
