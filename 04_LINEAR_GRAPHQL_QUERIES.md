# 04_LINEAR_GRAPHQL_QUERIES.md

## All GraphQL calls hit:
https://api.linear.app/graphql

Header:
Authorization: <LINEAR_API_KEY>
Content-Type: application/json

---

## 1) Get Epic by Identifier (<EPIC_IDENTIFIER>) + children
Use this to “hydrate” the epic and sub-issues with UUIDs and editable fields.

QUERY: EpicAndChildrenByIdentifier
Variables:
{ "identifier": "<EPIC_IDENTIFIER>" }

GraphQL (template):
query EpicAndChildrenByIdentifier($identifier: String!) {
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
- Keep the shape consistent with `epic_export.json` in the schemas doc.

---

## 2) Lookup State IDs / Label IDs by name (optional helper)
If you want to turn “In Progress” into a UUID, you can query workflow states.
(Only needed if you don’t already have IDs from the epic export.)

Example approach:
- Query team -> states
- Query labels by team or by search

Implementation varies per workspace; prefer using IDs already returned in export.