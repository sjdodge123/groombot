# 06_CREATE_SUB_ISSUES.md

## Goal
When grooming recommends **splitting** work, and the user confirms, Groombot should **create the new sub-issues in Linear** (not just describe them).

In Linear’s model, this means:
- **Parent issue** stays the same.
- Groombot creates **new sub-issues** under that parent issue using the Linear GraphQL API. citeturn0search0turn1view1

## When to create new sub-issues
Create new sub-issues when BOTH are true:
1) The grooming conversation recommends a split into distinct work items.
2) The user confirms they want those new work items created in Linear.

If the user does **not** confirm, Groombot should only propose the split in text and/or patch existing issues.

## Patch format for creations
If creating new sub-issues, the chat agent must add a `createSubIssues` list to `groom_patch.json`.

Example:

```json
{
  "meta": {
    "parentIssueIdentifier": "TEAM-123"
  },
  "changes": [],
  "createSubIssues": [
    {
      "title": "Add OAuth callback handler",
      "description": "Implement the callback route and error handling.",
      "estimate": 2,
      "splitFromIdentifier": "TEAM-124"
    },
    {
      "title": "Persist tokens securely",
      "description": "Store refresh/access tokens with encryption at rest.",
      "estimate": 3,
      "splitFromIdentifier": "TEAM-124"
    }
  ]
}
```

### Notes
- `splitFromIdentifier` is optional but recommended. It makes reviews/audits easy later.
- Keep `changes` as-is for updates to existing issues. Creation is a **separate** section.

## Script: create_sub_issues.py
Use `./scripts/create_sub_issues.py` to create the sub-issues in Linear. It:
- reads `createSubIssues` from `groom_patch.json`
- looks up the correct team from the parent issue
- creates each new issue with `issueCreate` and sets `parentId` to the parent issue ID (so the new issue is a sub-issue). citeturn1view1turn0search12turn0search14

### Dry-run (recommended first)
```bash
python3 ./scripts/create_sub_issues.py   --patch ./input-output-data/groom_patch.json   --export ./input-output-data/parent_issue_export.json   --dry-run
```

### Create for real
```bash
python3 ./scripts/create_sub_issues.py   --patch ./input-output-data/groom_patch.json   --export ./input-output-data/parent_issue_export.json
```

Outputs:
- `./input-output-data/create_report.json` (default)
- created issue identifiers and ids (for traceability)

## Suggested order of operations
If the patch contains BOTH updates and creations:

1) Export parent issue
2) Groom + produce `groom_patch.json`
3) **Create new sub-issues** (from `createSubIssues`)
4) Apply updates (`changes`) via `apply_patch.py`
5) Re-export parent issue (optional but recommended) to confirm everything looks right

## Architecture context
When proposing or confirming splits, ensure the project has an **Architecture Definition** issue (or `architecture.md` is provided for this run). This improves consistency across sessions. See `07_ARCHITECTURE_ANCHOR.md`.
