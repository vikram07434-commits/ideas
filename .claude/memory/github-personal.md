---
name: github-personal
description: Personal GitHub is github.com (not github.tools.sap which is SAP internal)
metadata:
  type: reference
---

Personal projects use https://github.com — the user's personal GitHub account.
- Account: vikram07434-commits
- Repo: https://github.com/vikram07434-commits/ideas
- Token: classic PAT "claude-ideas-workspace" (expires Aug 15, 2026, scopes: repo + workflow)
- Auth: embedded in git remote URL — `git push` works directly

SAP internal GitHub (github.tools.sap) is only for SAP work in other project directories.
When in the "ideas" workspace, always target github.com for pushes and remote setup.
