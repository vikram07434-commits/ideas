# Personal Creative Space — Local Rules

> This folder is a **personal sandbox** for ideation, exploration, and building new agents/apps.
> It is NOT an SAP project. None of the SAP-specific rules from the global CLAUDE.md apply here.

---

## Override: SAP Rules DO NOT APPLY

The following global rules are **explicitly disabled** in this workspace:

- SAP System Safety Rules — no SAP system is involved
- ABAP Development Rules — no ABAP here
- SAP MCP tools restrictions — we don't use them here
- "Always start with PLAN MODE" — optional here, use when it makes sense
- "Always show diff before every file edit" — not required, you have full write access
- "Always write output to .md files" — write code directly, this is a dev workspace

---

## What This Space IS

- A **personal lab** for ideating, prototyping, and building agents and apps
- Each idea/project lives in its own subfolder as a **separate project**
- Full read/write/execute access to this folder and all subfolders
- Freedom to create files, run code, install dependencies, build things

---

## GitHub

- **Repository**: https://github.com (personal GitHub, NOT github.tools.sap)
- Every project created here should be version-controlled
- Use `git init` for new projects, commit regularly
- Push to personal GitHub when ready

---

## Working Style

- **Be creative and proactive** — suggest ideas, explore possibilities
- **Build fast** — prototype first, polish later
- **No bureaucracy** — no plans required for small things, just build
- For larger projects, a brief plan is fine but keep it lightweight
- **Comments in code**: minimal, only when non-obvious
- **Testing**: appropriate to project size — unit tests for libraries, manual testing for prototypes

---

## Project Structure

```
ideas/
├── .claude/CLAUDE.md          ← this file (local rules)
├── CONTEXT.md                 ← workspace context & project index
├── project-a/                 ← each project in its own folder
├── project-b/
└── ...
```

---

## Security

- `.env` files rule still applies — never read/display secrets
- Be careful with API keys in committed code
- Use `.gitignore` properly for each project
