# 03_SCHEMAS_EXPORT_AND_PATCH.md

## A) Export Schema (parent_issue_export.json)
This is the normalized shape you want saved from GraphQL export.

{
  "meta": {
    "exportedAt": "ISO-8601",
    "workspace": "string",
    "source": "linear-graphql",
    "parentIssueIdentifier": "<PARENT_ISSUE_IDENTIFIER>",
    "parentIssueId": "uuid"
  },
  "parent issue": {
    "id": "uuid",
    "identifier": "<PARENT_ISSUE_IDENTIFIER>",
    "title": "string",
    "description": "string|null",
    "priority": 0,
    "estimate": 0,
    "state": { "id": "uuid", "name": "string" },
    "labels": [{ "id": "uuid", "name": "string" }],
    "assignee": { "id": "uuid", "name": "string" } | null,
    "updatedAt": "ISO-8601"
  },
  "subIssues": [
    {
      "id": "uuid",
      "identifier": "ENG-124",
      "title": "string",
      "description": "string|null",
      "priority": 0,
      "estimate": 0,
      "state": { "id": "uuid", "name": "string" },
      "labels": [{ "id": "uuid", "name": "string" }],
      "assignee": { "id": "uuid", "name": "string" } | null,
      "updatedAt": "ISO-8601"
    }
  ]
}

Notes:
- Keep both UUID `id` and human `identifier`.
- stateId/labelIds must be pulled from objects.

---

## B) Patch Schema (groom_patch.json)
This is what grooming produces and what the patch applier consumes.

{
  "meta": {
    "generatedAt": "ISO-8601",
    "parentIssueId": "uuid",
    "parentIssueIdentifier": "<PARENT_ISSUE_IDENTIFIER>",
    "mode": "apply",
    "notes": "string optional",
    "groomingSummary": {
      "ready": ["<PARENT_ISSUE_IDENTIFIER>", "<PARENT_ISSUE_IDENTIFIER>"],
      "needsClarification": ["<PARENT_ISSUE_IDENTIFIER>"],
      "blocked": ["<PARENT_ISSUE_IDENTIFIER>"],
      "splitRecommended": ["<PARENT_ISSUE_IDENTIFIER>"]
    }
  },
  "changes": [
    {
      "id": "uuid",
      "identifier": "<PARENT_ISSUE_IDENTIFIER>",
      "update": {
        "title": "string optional",
        "description": "string optional",
        "priority": 0,
        "estimate": 0,
        "stateId": "uuid optional",
        "assigneeId": "uuid|null optional",
        "labelIds": ["uuid", "uuid"]
      }
    }
  ],
  "session": {
    "parentIssueChatId": "string optional",
    "operator": "string optional",
    "openQuestions": ["string"],
    "decisions": ["string"]
  }
}

Rules:
- Only include fields inside `update` that you intend to change.
- Prefer labelIds/stateId/assigneeId as UUIDs (not names).
- If a field should be cleared, include it explicitly:
  - "assigneeId": null

---

## C) Patch Schema Extensions (Create new sub-issues)

Groombot supports **creating** new sub-issues during grooming by adding an optional `createSubIssues` array to `groom_patch.json`.

This does **not** replace `changes`. Use both when needed.

### `createSubIssues` shape
```json
{
  "createSubIssues": [
    {
      "title": "string (required)",
      "description": "string|null (optional)",
      "estimate": "number (optional)",
      "splitFromIdentifier": "string (optional, e.g. TEAM-124)"
    }
  ]
}
```

### Creation behavior
- New issues are created via the GraphQL `issueCreate` mutation. citeturn1view1
- Each new issue is created under the **same team** as the parent issue.
- Each new issue is created with `parentId = parentIssueId`, which makes it a **sub-issue**. citeturn0search12turn0search14

### Outputs
Creation writes `create_report.json` (see `06_CREATE_SUB_ISSUES.md`).
