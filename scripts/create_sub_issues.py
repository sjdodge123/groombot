#!/usr/bin/env python3
"""Create new sub-issues in Linear based on `createSubIssues` in groom_patch.json.

This script is intentionally separate from apply_patch.py:
- apply_patch.py updates existing issues
- create_sub_issues.py creates *new* issues when a split is confirmed
"""

import argparse
import hashlib
import json
import os
import sys
import time
from typing import Any, Dict, List, Optional
import urllib.request

LINEAR_ENDPOINT = "https://api.linear.app/graphql"

QUERY_PARENT_TEAM = """
query ParentIssueTeam($id: String!) {
  issue(id: $id) {
    id
    identifier
    team {
      id
      key
      name
    }
  }
}
"""

MUTATION_ISSUE_CREATE = """
mutation IssueCreate($input: IssueCreateInput!) {
  issueCreate(input: $input) {
    success
    issue {
      id
      identifier
      title
      url
    }
  }
}
"""

def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def load_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path: str, data: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def graphql_request(api_key: str, query: str, variables: Dict[str, Any]) -> Dict[str, Any]:
    payload = json.dumps({"query": query, "variables": variables}).encode("utf-8")
    req = urllib.request.Request(
        LINEAR_ENDPOINT,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": api_key,
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))

def backoff_sleep(attempt: int) -> None:
    # 0, 1, 2, 4, 8 seconds (cap)
    time.sleep(min(8, 2 ** max(0, attempt - 1)))

def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--patch", required=True, help="Path to groom_patch.json")
    p.add_argument("--export", required=True, help="Path to parent_issue_export.json")
    p.add_argument("--out", default=None, help="Path to create_report.json output (default: alongside --patch)")
    p.add_argument("--dry-run", action="store_true", help="Do not create; only print what would be created")
    args = p.parse_args()

    if args.out is None:
        patch_dir = os.path.dirname(os.path.abspath(args.patch)) or "."
        args.out = os.path.join(patch_dir, "create_report.json")

    api_key = os.environ.get("LINEAR_API_KEY")
    if not api_key:
        print("ERROR: LINEAR_API_KEY is not set.")
        return 2

    patch_data = load_json(args.patch)
    export_data = load_json(args.export)

    create_items: List[Dict[str, Any]] = patch_data.get("createSubIssues") or []
    if not create_items:
        print("No createSubIssues entries found. Nothing to create.")
        return 0

    parent_issue_id = (
        (patch_data.get("meta") or {}).get("parentIssueId")
        or (export_data.get("meta") or {}).get("parentIssueId")
    )
    parent_issue_identifier = (
        (patch_data.get("meta") or {}).get("parentIssueIdentifier")
        or (export_data.get("meta") or {}).get("parentIssueIdentifier")
    )

    if not parent_issue_id:
        print("ERROR: parentIssueId is missing. It must be present in patch.meta or export.meta.")
        return 1

    # Fetch team info for the parent issue so we can create in the correct team.
    team_id: Optional[str] = None
    team_key: Optional[str] = None
    team_name: Optional[str] = None

    resp = graphql_request(api_key, QUERY_PARENT_TEAM, {"id": parent_issue_id})
    if resp.get("errors"):
        print("ERROR: Linear API returned errors while fetching parent issue team:")
        print(json.dumps(resp["errors"], indent=2))
        return 1

    issue = (resp.get("data") or {}).get("issue")
    if not issue:
        print("ERROR: Could not load parent issue by id. Check parentIssueId and API key/workspace.")
        return 1

    team = (issue.get("team") or {})
    team_id = team.get("id")
    team_key = team.get("key")
    team_name = team.get("name")

    if not team_id:
        print("ERROR: Could not resolve teamId for the parent issue.")
        return 1

    # Create loop
    results: List[Dict[str, Any]] = []

    for idx, item in enumerate(create_items, start=1):
        title = (item.get("title") or "").strip()
        if not title:
            results.append({"index": idx, "success": False, "error": "Missing required field: title"})
            continue

        input_obj: Dict[str, Any] = {
            "title": title,
            "teamId": team_id,
            "parentId": parent_issue_id,
        }

        if item.get("description") is not None:
            input_obj["description"] = item.get("description")
        if item.get("estimate") is not None:
            input_obj["estimate"] = item.get("estimate")

        split_from = item.get("splitFromIdentifier")

        if args.dry_run:
            print(f"[DRY RUN] Would create sub-issue under {parent_issue_identifier or parent_issue_id}: {title}")
            results.append({
                "index": idx,
                "success": None,
                "dryRun": True,
                "title": title,
                "splitFromIdentifier": split_from,
                "created": None
            })
            continue

        success = False
        err: Optional[str] = None
        created: Optional[Dict[str, Any]] = None

        for attempt in range(0, 5):
            try:
                out = graphql_request(api_key, MUTATION_ISSUE_CREATE, {"input": input_obj})
                if out.get("errors"):
                    err = json.dumps(out["errors"])
                    success = False
                else:
                    data = (out.get("data") or {}).get("issueCreate") or {}
                    success = bool(data.get("success"))
                    created = data.get("issue")
                    if not success:
                        err = "Mutation returned success=false"
                break
            except Exception as e:
                err = str(e)
                backoff_sleep(attempt)
                continue

        results.append({
            "index": idx,
            "success": success,
            "error": err,
            "title": title,
            "splitFromIdentifier": split_from,
            "created": created,
        })

    report = {
        "meta": {
            "createdAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "parentIssueIdentifier": parent_issue_identifier or issue.get("identifier"),
            "parentIssueId": parent_issue_id,
            "team": {"id": team_id, "key": team_key, "name": team_name},
            "patchFileSha256": sha256_file(args.patch),
            "exportFileSha256": sha256_file(args.export),
            "dryRun": bool(args.dry_run),
        },
        "creates": results,
    }

    save_json(args.out, report)
    print(f"Wrote {args.out}")

    failed = [r for r in results if r.get("success") is False]
    if failed:
        print("WARNING: Some creations failed. See create_report.json for details.")
        return 1

    return 0

if __name__ == "__main__":
    raise SystemExit(main())
