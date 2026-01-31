# 03_SCHEMAS_EXPORT_AND_PATCH.md

## A) Export Schema (epic_export.json)
This is the normalized shape you want saved from GraphQL export.

{
  "meta": {
    "exportedAt": "ISO-8601",
    "workspace": "string",
    "source": "linear-graphql",
    "epicIdentifier": "<EPIC_IDENTIFIER>",
    "epicId": "uuid"
  },
  "epic": {
    "id": "uuid",
    "identifier": "<EPIC_IDENTIFIER>",
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
    "epicId": "uuid",
    "epicIdentifier": "<EPIC_IDENTIFIER>",
    "mode": "apply",
    "notes": "string optional",
    "groomingSummary": {
      "ready": ["<EPIC_IDENTIFIER>", "<EPIC_IDENTIFIER>"],
      "needsClarification": ["<EPIC_IDENTIFIER>"],
      "blocked": ["<EPIC_IDENTIFIER>"],
      "splitRecommended": ["<EPIC_IDENTIFIER>"]
    }
  },
  "changes": [
    {
      "id": "uuid",
      "identifier": "<EPIC_IDENTIFIER>",
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
    "epicChatId": "string optional",
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