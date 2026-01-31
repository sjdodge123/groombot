#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   ./scripts/export_epic.sh <EPIC_IDENTIFIER>
# Example:
#   ./scripts/export_epic.sh ROK-26

if [[ $# -ne 1 ]]; then
  echo "Usage: ./scripts/export_epic.sh <EPIC_IDENTIFIER>"
  exit 2
fi

EPIC_IDENTIFIER="$1"

if [[ -z "${LINEAR_API_KEY:-}" ]]; then
  echo "ERROR: LINEAR_API_KEY is not set."
  exit 2
fi

if [[ ! "$EPIC_IDENTIFIER" =~ ^([A-Za-z]+)-([0-9]+)$ ]]; then
  echo "ERROR: Epic identifier must look like TEAM-123 (e.g., ROK-26). Got: $EPIC_IDENTIFIER"
  exit 1
fi

TEAM_KEY="${BASH_REMATCH[1]}"
ISSUE_NUMBER="${BASH_REMATCH[2]}"

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

CACHE_DIR="${ROOT_DIR}/local-cache"
CACHE_OUT_FILE="${CACHE_DIR}/epic_export.json"

IO_DIR="${ROOT_DIR}/input-output-data"
IO_OUT_FILE="${IO_DIR}/epic_export.json"

mkdir -p "$CACHE_DIR" "$IO_DIR"

TMP_PAYLOAD="$(mktemp -t linear_payload.XXXXXX.json)"
TMP_RESP="$(mktemp -t linear_resp.XXXXXX.json)"
cleanup() {
  rm -f "$TMP_PAYLOAD" "$TMP_RESP"
}
trap cleanup EXIT

# NOTE:
# IssueFilter does NOT support filtering by identifier. We filter by team.key + number instead.
cat > "$TMP_PAYLOAD" <<JSON
{
  "query": "query EpicByTeamAndNumber(\$teamKey: String!, \$issueNumber: Float!) { issues(filter: { team: { key: { eq: \$teamKey } }, number: { eq: \$issueNumber } }, first: 1) { nodes { id identifier title description estimate updatedAt state { id name } labels { nodes { id name } } assignee { id name email } team { id key name } children(first: 250) { nodes { id identifier title description estimate updatedAt state { id name } labels { nodes { id name } } assignee { id name email } } } } } }",
  "variables": { "teamKey": "${TEAM_KEY}", "issueNumber": ${ISSUE_NUMBER} }
}
JSON

curl -sS https://api.linear.app/graphql \
  -H "Content-Type: application/json" \
  -H "Authorization: ${LINEAR_API_KEY}" \
  --data @"${TMP_PAYLOAD}" \
  > "${TMP_RESP}"

python3 - "$EPIC_IDENTIFIER" "$TMP_RESP" "$CACHE_OUT_FILE" "$IO_OUT_FILE" <<'PY'
import json, sys
from datetime import datetime, timezone

identifier = sys.argv[1]
resp_path = sys.argv[2]
cache_out = sys.argv[3]
root_out = sys.argv[4]

with open(resp_path, "r", encoding="utf-8") as f:
    resp = json.load(f)

if "errors" in resp and resp["errors"]:
    print("ERROR: Linear API returned errors:")
    print(json.dumps(resp["errors"], indent=2))
    sys.exit(1)

nodes = (((resp.get("data") or {}).get("issues") or {}).get("nodes") or [])
if not nodes:
    print("ERROR: No issue found for identifier:", identifier)
    sys.exit(1)

issue = nodes[0]

children = (((issue.get("children") or {}).get("nodes")) or [])
filtered = [c for c in children if ((c.get("state") or {}).get("name") == "Backlog")]

def label_nodes(obj):
    return [ {"id": n["id"], "name": n["name"]} for n in (((obj.get("labels") or {}).get("nodes")) or []) ]

export = {
  "meta": {
    "exportedAt": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    "workspace": None,
    "source": "linear-graphql",
    "epicIdentifier": issue["identifier"],
    "epicId": issue["id"],
    "subIssueFilter": {
      "stateNameEq": "Backlog"
    }
  },
  "epic": {
    "id": issue["id"],
    "identifier": issue["identifier"],
    "title": issue["title"],
    "description": issue.get("description"),
    "state": (issue.get("state") or {}).get("name"),
    "estimate": issue.get("estimate"),
    "labels": label_nodes(issue),
    "assignee": issue.get("assignee"),
    "updatedAt": issue["updatedAt"],
  },
  "subIssues": []
}

for ch in filtered:
  export["subIssues"].append({
    "id": ch["id"],
    "identifier": ch["identifier"],
    "title": ch["title"],
    "description": ch.get("description"),
    "state": (ch.get("state") or {}).get("name"),
    "estimate": ch.get("estimate"),
    "labels": label_nodes(ch),
    "assignee": ch.get("assignee"),
    "updatedAt": ch["updatedAt"],
  })

with open(cache_out, "w", encoding="utf-8") as f:
  json.dump(export, f, indent=2)

with open(root_out, "w", encoding="utf-8") as f:
  json.dump(export, f, indent=2)

print(f"Wrote {cache_out} (cache) and {root_out} (upload copy) for epic {issue['identifier']}.")
print(f"Included {len(filtered)} Backlog sub-issues out of {len(children)} total sub-issues.")
PY