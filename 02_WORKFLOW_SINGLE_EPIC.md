# 02_WORKFLOW_SINGLE_EPIC.md

## Goal
Run grooming for exactly ONE epic (parent issue) and its sub-issues at a time.

## Session Steps (repeat per epic)

### Step 0 — Preflight (local)
- Confirm `LINEAR_API_KEY` exists.
- Confirm local-cache files exist and are writable.

### Step 1 — Export the epic (local)
- Fetch the epic and its sub-issues from Linear GraphQL.
- Save result as: `epic_export.json`
- The export MUST include:
  - issue UUID `id`
  - human key `identifier` (e.g., <EPIC_IDENTIFIER>)
  - title, description
  - state (id, name)
  - labels (ids, names)
  - priority, estimate
  - assignee (id, name)
  - children issues list (sub-issues)
  - updatedAt

### Step 2 — Groom (in ChatGPT or locally)
Use the Grooming Rubric:
1) Title clarity:
   - format: Verb + Object + Qualifier
2) Scope:
   - identify multi-scope items, propose splits
3) Acceptance Criteria:
   - 3–7 bullets per issue
4) Estimation:
   - S/M/L or numeric estimate (your team preference)
5) Labels / Priority:
   - suggest consistent tagging

Deliverables from grooming:
- A proposed set of changes for:
  - parent epic issue
  - each sub-issue
- A list of open questions / blockers if any
- A “Ready / Needs Clarification / Blocked / Split Recommended” summary

### Step 3 — Produce patch JSON (per epic)
Create: `groom_patch.json` matching schema in `03_SCHEMAS_EXPORT_AND_PATCH.md`.

Rules:
- Patch MUST be id-based (UUID `id`).
- Patch SHOULD only include fields that changed.
- Patch MUST include a session metadata block.

### Step 4 — Apply patch (local)
- Run dry-run: preview changes vs current Linear fields (best effort).
- Apply patch mutations issue-by-issue.
- Capture results (success/failure) to an apply report JSON.

### Step 5 — Update local-cache (local)
Write:
- Epic marked groomed with timestamp, patch hash (optional), and issue list.
- Each issue marked groomed with what was changed.

### Step 6 — Handoff Notes (for the next agent)
If anything was left unresolved:
- Record in local-cache “notes” fields:
  - open questions
  - decisions made
  - items to re-check next session