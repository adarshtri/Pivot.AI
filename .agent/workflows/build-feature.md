---
description: How to build a new feature or API
---
# Feature Development Workflow

When asked to build a new feature for Pivot.AI, always follow these parallel-development and decoupled steps:

1. **Design the Interface & Data Layer first**: 
   - Define what data the new feature needs and where it sits in the multi-tenant architecture. Ensure separation between Data Plane and Control Plane.
2. **Implement the API & Logic**: 
   - Build out the API endpoints in FastAPI. Make sure AI semantics are cleanly decoupled and delivery channels remain interface-driven.
3. **Immediately Build Minimal UI**: 
   - Do not stop at the backend. You must immediately build a minimal CLI, Telegram interaction, or UI web component to validate the endpoint end-to-end.
4. **Validate**:
   - Test the feature from the perspective of an end-user to ensure smooth onboarding and lack of technical friction.
