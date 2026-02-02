# 02_WORKFLOW_SINGLE_PARENT_ISSUE.md

## Goal
Run grooming for exactly ONE Issue (parent issue) and its sub-issues at a time.


## Step 2 — Confirm the project has an Architecture Definition issue
After exporting the parent issue, ensure the Linear *project* in scope has a single top-level **Architecture Definition** issue (no parent).

- If it exists: read it and treat it as the authoritative architectural context.
- If it does not exist: pause and ask the operator for `architecture.md` (or let them opt to provide it each run).

Helper script (safe to run repeatedly):
```bash
python3 ./scripts/ensure_architecture_issue.py \
  --export ./input-output-data/parent_issue_export.json \
  --dry-run
```

Reference: `07_ARCHITECTURE_ANCHOR.md`.

## Session Steps (repeat per Issue)

### Step 0 — Preflight (local)
- Confirm `LINEAR_API_KEY` exists.
- Confirm local-cache files exist and are writable.

### Step 1 — Export the parent issue (local)
- Fetch the parent issue and its sub-issues from Linear GraphQL.
- Save result as: `parent_issue_export.json`
- The export MUST include:
  - issue UUID `id`
  - human key `identifier` (e.g., <PARENT_ISSUE_IDENTIFIER>)
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
  - parent parent issue issue
  - each sub-issue
- A list of open questions / blockers if any
- A “Ready / Needs Clarification / Blocked / Split Recommended” summary

### Step 3 — Produce patch JSON (per parent issue)
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
- Parent issue marked groomed with timestamp, patch hash (optional), and issue list.
- Each issue marked groomed with what was changed.

### Step 6 — Handoff Notes (for the next agent)
If anything was left unresolved:
- Record in local-cache “notes” fields:
  - open questions
  - decisions made
  - items to re-check next session

### Step 2.5 — If a split is recommended and confirmed (chat + local)
If the grooming conversation recommends splitting an issue into multiple smaller work items **and the user confirms**, the agent MUST:
1) Add a `createSubIssues` array to `groom_patch.json` describing the new work items (title/description/estimate).
2) Instruct the user to run `create_sub_issues.py` to create those new sub-issues in Linear.

See: `06_CREATE_SUB_ISSUES.md`.

Why: the goal is to minimize expensive coding-model time by having the groomer do the decomposition AND create the resulting issues directly in Linear.