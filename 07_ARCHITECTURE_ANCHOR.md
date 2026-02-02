# 07_ARCHITECTURE_ANCHOR.md

## Goal
Before you groom any work in a Linear **project**, ensure there is a single, consistent **Architecture Definition** in the project's **Resources**.

This creates a stable reference point so every future Groombot session can reason from the same architectural ground truth.

## Primary Location: Project Documents (Resources)
The preferred location for architecture is a **Project Document** named `architecture.md`.
This appears in the "Resources" tab of the project in Linear.

## Secondary Location: Architecture Issue (Legacy)
For backward compatibility, Groombot will also look for a top-level **Architecture Definition** issue if no document is found.

## Workflow

> This step happens **after** you export the parent issue.

### 1) Check for the architecture anchor
Run the helper script:

```bash
python3 ./scripts/ensure_architecture_issue.py \
  --export ./input-output-data/parent_issue_export.json \
  --dry-run
```

This will:
1.  Search `Project.documents` for `architecture.md` (Success).
2.  If missing, search `Project.issues` for "Architecture Definition" (Fallback).
3.  If both missing, report missing.

### 2) If missing:
Groombot will ask you to provide an `architecture.md` file.

### 3) Create it (only after operator confirmation)
If provided, Groombot will create it as a **Project Document**:

```bash
python3 ./scripts/ensure_architecture_issue.py \
  --export ./input-output-data/parent_issue_export.json \
  --architecture-file ./architecture.md
```

This ensures the architecture becomes a permanent resource of the project.
