# 💎 Dynamic Career Resources

Pivot.AI allows you to give the Agent personal context without hardcoding any data. By placing Markdown or text files in your resources directory, the Agent "learns" about your goals, preferences, and history.

## 📂 Resource Directory
All context files should be stored at:
`~/.pivot-ai/resources/`

## 🚀 How it Works
1.  **Startup Discovery**: On launch, the CLI scans this folder. Any `.md` or `.txt` file found is automatically registered as a protocol-native MCP resource.
2.  **URI Mapping**: Files are mapped to a custom URI scheme: `pivot://user/{filename}`.
3.  **On-Demand Access**: The Agent doesn't read every file at once (to save tokens). Instead, it "knows" what files exist and will only [read_resource] when it needs specific information to answer your question.

## 📝 Example: `goals.md`
Create a file named `goals.md` with your career objectives:
```markdown
# My Career Goals
- Move into a Staff Engineer role by 2026.
- Focus on Distributed Systems and Rust.
- Preference for remote-first companies.
```

When you ask the Agent "What are my goals?", it will:
1.  Search the registry for `goals.md`.
2.  Use the `read_resource` skill to fetch the content.
3.  Provide a summarized response based on your file.

---

## 🛠️ Dynamic Updates
If you add a file **after** the CLI is already running:
1.  Use the `list_resources` tool to see the new addition.
2.  The Agent can then use the URI template `pivot://user/{new_file.md}` to read it.

> [!TIP]
> Keep your resource files focused. Use one file for `resume.md`, another for `technical-preferences.md`, and another for `target-companies.md`.
