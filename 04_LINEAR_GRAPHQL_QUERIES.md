# 04_LINEAR_GRAPHQL_QUERIES.md

## All GraphQL calls hit:
https://api.linear.app/graphql

Header:
Authorization: <LINEAR_API_KEY>
Content-Type: application/json

---

## 1) Get Parent issue by Identifier (<PARENT_ISSUE_IDENTIFIER>) + children
Use this to “hydrate” the parent issue and sub-issues with UUIDs and editable fields.

QUERY: ParentIssueAndChildrenByIdentifier
Variables:
{ "identifier": "<PARENT_ISSUE_IDENTIFIER>" }

GraphQL (template):
query ParentIssueAndChildrenByIdentifier($identifier: String!) {
  issue(identifier: $identifier) {
    id
    identifier
    title
    description
    priority
    estimate
    updatedAt
    assignee { id name }
    state { id name }
    labels { nodes { id name } }

    # Children / sub-issues
    children {
      nodes {
        id
        identifier
        title
        description
        priority
        estimate
        updatedAt
        assignee { id name }
        state { id name }
        labels { nodes { id name } }
      }
    }
  }
}

Notes:
- If your workspace uses “relations” differently, you may need to adjust children field naming.
- Keep the shape consistent with `parent_issue_export.json` in the schemas doc.

---


---

## 2) Lookup State IDs / Label IDs by name (optional helper)
If you want to turn “In Progress” into a UUID, you can query workflow states.

### Process
1.  Identify the Team ID from the parent issue.
2.  Query `team.states`.

### Helper Script
```bash
python3 ./scripts/fetch_workflow_states.py
```

### GraphQL Query
```graphql
query GetTeamStates($teamId: String!) {
  team(id: $teamId) {
    id
    name
    states {
      nodes {
        id
        name
        type
        color
      }
    }
  }
}
```

## 3) Common State Mappings (Reference)
*Auto-generated from recent runs. Validate before use.*

| State Name | Type | UUID |
| :--- | :--- | :--- |
| **Backlog** | backlog | `486a58cf-2f7c-48ab-9990-33ae517af6db` |
| **Todo** | unstarted | `c22b469d-0eb9-49b6-9260-032f766a7fd3` |
| **In Progress** | started | `f18c0a0e-bd50-4bc5-b91a-466725053d77` |
| **In Review** | started | `f4c7c4d6-9ffb-43ce-a578-41f21eb0824d` |
| **Done** | completed | `6a83698b-72de-4a25-ab81-2d820c5a6b04` |
| **Canceled** | canceled | `5721ae30-f12e-47eb-a9cd-528abe850bae` |
| **Duplicate** | canceled | `34f1b9cc-61a4-4186-8c0c-9a53e68ca605` |