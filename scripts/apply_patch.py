#!/usr/bin/env python3
import argparse
import datetime as dt
import hashlib
import json
import os
import sys
import time
from typing import Any, Dict, List, Optional
import urllib.request

LINEAR_ENDPOINT = "https://api.linear.app/graphql"

MUTATION = """
mutation IssueUpdate($id: String!, $input: IssueUpdateInput!) {
  issueUpdate(id: $id, input: $input) {
    success
    issue { id identifier title updatedAt }
  }
}
"""

def utc_now() -> str:
    return dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

def load_json(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path: str, obj: Any) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2)

def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

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
        data = resp.read().decode("utf-8")
        return json.loads(data)

def backoff_sleep(attempt: int) -> None:
    # simple exponential backoff with cap
    delay = min(2 ** attempt, 16)
    time.sleep(delay)

def update_cache(cache_dir: str, export_data: Dict[str, Any], patch_data: Dict[str, Any], apply_report_path: str) -> None:
    epics_path = os.path.join(cache_dir, "groomed_epics.json")
    issues_path = os.path.join(cache_dir, "groomed_issues.json")

    # load existing
    epics = load_json(epics_path)
    issues = load_json(issues_path)

    epic = export_data["epic"]
    epic_identifier = epic["identifier"]
    epic_id = epic["id"]

    patch_hash = sha256_file(apply_report_path)  # tie cache to actual apply report

    # record epic-level
    epics["epics"].append({
        "epicId": epic_id,
        "epicIdentifier": epic_identifier,
        "title": epic["title"],
        "groomedAt": utc_now(),
        "status": "groomed",
        "appliedPatch": True,
        "applyReportPath": os.path.relpath(apply_report_path, os.path.dirname(cache_dir)),
        "patchMeta": patch_data.get("meta", {}),
        "patchApplyReportSha256": patch_hash,
        "issues": [ch.get("identifier") for ch in export_data.get("subIssues", [])],
        "openQuestions": (patch_data.get("session") or {}).get("openQuestions", []),
        "decisions": (patch_data.get("session") or {}).get("decisions", []),
        "notes": (patch_data.get("meta") or {}).get("notes"),
    })

    # record issue-level changes only for issues in patch
    changed_by_id = {c["id"]: c for c in patch_data.get("changes", [])}

    # helper index of export issues
    export_issues = [export_data["epic"]] + export_data.get("subIssues", [])
    export_by_id = {it["id"]: it for it in export_issues}

    for issue_id, change in changed_by_id.items():
        before = export_by_id.get(issue_id, {})
        update = change.get("update", {})
        changed_fields = list(update.keys())

        issues["issues"].append({
            "id": issue_id,
            "identifier": change.get("identifier") or before.get("identifier"),
            "parentEpicIdentifier": epic_identifier,
            "groomedAt": utc_now(),
            "appliedPatch": True,
            "changedFields": changed_fields,
            "before": {k: before.get(k) for k in changed_fields},
            "after": update,
            "notes": None,
        })

    save_json(epics_path, epics)
    save_json(issues_path, issues)
    print(f"Updated cache: {epics_path}, {issues_path}")

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--patch", required=True, help="Path to groom_patch.json")
    parser.add_argument("--export", required=True, help="Path to epic_export.json (snapshot used for diff/cache)")
    parser.add_argument("--out", default=None, help="Path to apply_report.json output (default: alongside --export)")
    parser.add_argument("--cache-dir", default="local-cache", help="Cache directory (default: local-cache)")
    parser.add_argument("--dry-run", action="store_true", help="Do not apply changes; only print what would change")
    args = parser.parse_args()

    # Default apply_report.json to the same directory as the export file
    if args.out is None:
        export_dir = os.path.dirname(os.path.abspath(args.export)) or "."
        args.out = os.path.join(export_dir, "apply_report.json")

    # Ensure output directory exists
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)

    api_key = os.environ.get("LINEAR_API_KEY", "")
    if not api_key:
        print("ERROR: LINEAR_API_KEY not set. Run: source ~/.zshrc", file=sys.stderr)
        return 2

    patch_data = load_json(args.patch)
    export_data = load_json(args.export)

    changes: List[Dict[str, Any]] = patch_data.get("changes", [])
    if not changes:
        print("No changes found in patch. Nothing to do.")
        return 0

    results = []
    for c in changes:
        issue_id = c["id"]
        identifier = c.get("identifier")
        update = c.get("update", {})

        if args.dry_run:
            print(f"[DRY RUN] Would update {identifier or issue_id}: {list(update.keys())}")
            results.append({"identifier": identifier, "id": issue_id, "success": None, "error": None, "dryRun": True})
            continue

        success = False
        err: Optional[str] = None

        # retry loop
        for attempt in range(0, 5):
            try:
                resp = graphql_request(api_key, MUTATION, {"id": issue_id, "input": update})
                if "errors" in resp:
                    err = json.dumps(resp["errors"])
                    success = False
                else:
                    out = resp.get("data", {}).get("issueUpdate", {})
                    success = bool(out.get("success"))
                    if not success:
                        err = f"Mutation returned success=false for {identifier or issue_id}"
                break
            except Exception as e:
                err = str(e)
                backoff_sleep(attempt)
                continue

        results.append({"identifier": identifier, "id": issue_id, "success": success, "error": err})

    report = {
        "meta": {
            "appliedAt": utc_now(),
            "epicIdentifier": (patch_data.get("meta") or {}).get("epicIdentifier") or export_data.get("meta", {}).get("epicIdentifier"),
            "epicId": (patch_data.get("meta") or {}).get("epicId") or export_data.get("meta", {}).get("epicId"),
            "patchFileSha256": sha256_file(args.patch),
            "exportFileSha256": sha256_file(args.export),
            "dryRun": bool(args.dry_run),
        },
        "results": results,
    }
    save_json(args.out, report)
    print(f"Wrote {args.out}")

    if not args.dry_run:
        # only update cache if all applied successfully
        failed = [r for r in results if r["success"] is not True]
        if failed:
            print("WARNING: Some updates failed; cache will NOT be updated automatically.")
            print("Fix failures, re-run apply, then update cache.")
            return 1
        update_cache(args.cache_dir, export_data, patch_data, args.out)

    return 0

if __name__ == "__main__":
    raise SystemExit(main())