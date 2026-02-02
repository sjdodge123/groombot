# Groombot

## Purpose
This folder is a reusable pre-prompt and tooling bundle for running **Linear grooming sessions one parent issue at a time**.

An parent issue is defined as:
- A parent Issue in Linear
- With zero or more sub-issues (children)

Each session:
- Starts with a fresh agent/chat
- Exports the current parent issue state from Linear
- Grooms only that parent issue
- Applies a patch after grooming
- Updates a local cache so future agents know what has already been groomed

---

## Core Rules (Do Not Violate)
- Groom **exactly ONE parent issue per session**
- Never include comments on anything that is translated to the user in a copy+paste format. The comments mess up the terminal commands.
- Always export fresh data from Linear at the start
- Never groom without `parent_issue_export.json`
- Never invent identifiers, labels, states, or cache entries
- Never request or store API keys
- Apply patches only after grooming is complete

---

## Streamlined Agent-Led Session Flow

1) Upload the zipped `linear-grooming-kit/` folder to a **new chat agent**
2) The agent will:
   - read all docs
   - confirm understanding
   - ask which parent issue identifier to groom
   - wait for the response from operator before providing the scripts so that they include the provided parent issue identifer baked in
3) The agent will instruct the operator to run terminal commands to:
    *Important* Never provide comments in scripts provided
   - load environment variables
   - ensure scripts are executable
   - initialize cache (if needed)
   - export the parent issue into `parent_issue_export.json`
4) The operator uploads `parent_issue_export.json`
5) The agent walks through each issue tied to the parent issue, one by one
6) The agent understands the context of the issue and asks clarifying questions to add acceptance criteria, and intended scope before moving forward
5) The agent grooms the parent issue and produces `groom_patch.json`
6) The operator applies the patch locally
7) Cache is updated automatically by the script
8) The session ends
9) Start the next parent issue in a brand-new chat

---

## Script Permissions (Important)
If scripts are edited, copied, or checked out on a new machine,
re-run these commands:

```bash
chmod +x ./scripts/init_cache.sh
chmod +x ./scripts/export_parent_issue.sh
chmod +x ./scripts/apply_patch.py

## Architecture anchor issue
Groombot expects each Linear project to have a single top-level **Architecture Definition** issue. If it cannot be found, the operator should provide an `architecture.md` file so Groombot can create it (or provide the file each run). See `07_ARCHITECTURE_ANCHOR.md`.
