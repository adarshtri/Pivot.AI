# 📜 Dynamic SOPs (Playbooks)

Pivot.AI isn't just a chat bot—it is a **Procedural Agent**. You can define high-level Standard Operating Procedures (SOPs) as Markdown files, and the Agent will follow them as "guided workflows."

## 📂 SOP Directory
Define your "Playbooks" in:
`~/.pivot-ai/sops/`

## 🚀 How it Works
1.  **Auto-Discovery**: Any `.md` file in this folder becomes a selectable **Slash-Command** (e.g., `/analyze-match`).
2.  **Variable Injection**: Use `{{placeholder}}` in your Markdown to define required arguments. The CLI will ask you for values for these before starting.
3.  **Instruction Injection**: The Agent receives your Markdown instructions as its "Blueprint" and guided task.

## 📝 Example: `gap-analysis.md`
Create a file named `gap-analysis.md` with your procedure:
```markdown
# 📊 Gap Analysis
Compare my profile vs. job ID: {{job_id}}.

## INSTRUCTIONS:
1.  Read the user's `resume.md` from resources.
2.  Use the [score_job] tool for the provided ID.
3.  Cross-reference the job requirements with the resume and highlight technical skill gaps.
```

When you trigger this SOP using `[**`/gap-analysis job_id=123`**]`:
1.  The Agent is bootstapped with these specific instructions.
2.  The `{{job_id}}` placeholder is replaced with `123` automatically.
3.  The Agent will now follow the three-step plan you defined.

---

## 🛠️ Intentional Invocation
To keep the main chat clean, SOPs are only triggered **intentionally** via their slash commands. 

> [!IMPORTANT]
> **Variable Naming**: Always use lower_case for placeholders (e.g., `{{company_name}}`). When invoking, use the same name: `/analyze company_name=egen`.

> [!TIP]
> You can build SOPs for anything—Mock Interview Prep, Resume Tailoring, or Technical Research. Your imagination is the only limit to your Playbook's power.
