# Scripts Overview (Read This First)

This folder contains the executable scripts used to:
- export a single Linear parent issue + sub-issues
- apply a groomed patch back to Linear
- initialize and update the local grooming cache

These scripts are designed to be run locally from your terminal.
They rely on `LINEAR_API_KEY` being present in your shell environment.

## Agent-Led Sessions

In an agent-led grooming session:
- The agent is expected to instruct the human operator when to:
  - source ~/.zshrc
  - chmod scripts
  - run export_parent_issue.sh
- The agent must wait for parent_issue_export.json before grooming begins.

---

## Required Environment (every session)

1) Load your environment variables:
source ~/.zshrc

2) Verify Linear API key is available:
echo "$LINEAR_API_KEY"

If this prints nothing, STOP and fix your shell config before continuing.

---

## Script Permissions (IMPORTANT)

Executable permissions may be lost if:
- scripts are edited
- files are copied
- repo is cloned on a new machine

Run these commands ANY TIME scripts change:

chmod +x ./scripts/init_cache.sh
chmod +x ./scripts/export_parent_issue.sh
chmod +x ./scripts/apply_patch.py

You can safely re-run these at any time.

---

## One-Time (or First-Run) Setup

Initialize the local grooming cache:
./scripts/init_cache.sh

This creates (if missing):
- local-cache/groomed_parent_issues.json
- local-cache/groomed_issues.json

These files MUST remain real-data-only (no examples).

---

## Per-Parent issue Workflow (REPEAT FOR EACH PARENT ISSUE)

### Step 1 — Export current state from Linear
Export ONE parent issue (parent issue) and its sub-issues:

./scripts/export_parent_issue.sh ENG-123

Replace `ENG-123` with the parent issue identifier.

This writes:
- parent_issue_export.json (at the repo root)

---

### Step 2 — Groom (ChatGPT / agent step)
Upload:
- the zipped `linear-grooming-kit/`
- `parent_issue_export.json`

The agent will:
- groom the parent issue and sub-issues
- output `groom_patch.json`

Save `groom_patch.json` locally.

---

### Step 3 — Apply the groomed patch
Apply changes back to Linear and update cache:

python3 ./scripts/apply_patch.py \
  --patch groom_patch.json \
  --export parent_issue_export.json

This writes:
- apply_report.json

If ALL updates succeed, it automatically updates:
- local-cache/groomed_parent_issues.json
- local-cache/groomed_issues.json

---

## Dry Run (Preview Only)

To preview changes WITHOUT modifying Linear or cache:

python3 ./scripts/apply_patch.py \
  --patch groom_patch.json \
  --export parent_issue_export.json \
  --dry-run

Dry runs do NOT update Linear or cache files.

---

## Failure Handling

If any issue update fails:
- The script will report the failure in `apply_report.json`
- The local cache will NOT be updated automatically
- Fix the issue, re-run the patch, then proceed

Never manually edit cache files unless explicitly repairing state.

---

## Design Rules (Do Not Violate)

- One parent issue per session.
- Always export fresh data before grooming.
- Never store API keys in files or chat.
- Cache files must only reflect real applied changes.
- Always start the next parent issue in a new chat agent.

---

## Quick Checklist (Agent-Friendly)

- [ ] source ~/.zshrc
- [ ] chmod scripts if needed
- [ ] ./scripts/init_cache.sh
- [ ] ./scripts/export_parent_issue.sh <PARENT ISSUE>
- [ ] Upload parent_issue_export.json
- [ ] Groom + generate groom_patch.json
- [ ] python3 ./scripts/apply_patch.py ...
- [ ] Verify cache updated

---

## create_sub_issues.py (NEW)
Creates new sub-issues under a parent issue when grooming confirms a split.

Usage:
```bash
python3 ./scripts/create_sub_issues.py \
  --patch ./input-output-data/groom_patch.json \
  --export ./input-output-data/parent_issue_export.json \
  --dry-run

python3 ./scripts/create_sub_issues.py \
  --patch ./input-output-data/groom_patch.json \
  --export ./input-output-data/parent_issue_export.json
```

Outputs:
- `./input-output-data/create_report.json`

See `06_CREATE_SUB_ISSUES.md` for patch format.

### Ensure Architecture Definition issue (project anchor)
- `scripts/ensure_architecture_issue.py` — checks for (and can create) a top-level Architecture Definition issue in the project.
  - Dry run:
    ```bash
    python3 ./scripts/ensure_architecture_issue.py \
      --export ./input-output-data/parent_issue_export.json \
      --dry-run
    ```
  - Create from file (only after operator confirmation):
    ```bash
    python3 ./scripts/ensure_architecture_issue.py \
      --export ./input-output-data/parent_issue_export.json \
      --architecture-file ./architecture.md
    ```
  - See `07_ARCHITECTURE_ANCHOR.md`.
