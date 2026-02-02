#!/usr/bin/env python3
"""Ensure a project has a top-level Architecture Definition resources.

Why:
- Groombot grooming works best when every Linear project has a single, consistent place
  to reference the project's architecture assumptions and decisions.

What this script does:
1) Determines the *team* (and usually the *project*) from the parent issue export.
2) Searches the project's **Documents** for an existing `architecture.md`.
3) If missing, searches the project's **Issues** for an "Architecture Definition" issue (fallback).
4) If both are missing, it can create a **Project Document** from a local file (optional).

Notes:
- Storing `architecture.md` in Linear Project Resources (Documents) is the preferred method.
"""

import argparse
import json
import os
import sys
import time
from typing import Any, Dict, Optional
import urllib.request
import urllib.error


QUERY_PARENT_CONTEXT = """
query ParentIssueContext($id: String!) {
  issue(id: $id) {
    id
    identifier
    team { id key name }
    project { id name }
  }
}
"""

QUERY_PROJECTS = """
query Projects($first: Int!) {
  projects(first: $first) {
    nodes { id name }
  }
}
"""

QUERY_FIND_ARCH_DOC = """
query FindArchitectureDoc($projectId: String!, $title: String!) {
  project(id: $projectId) {
    documents(filter: { title: { eq: $title } }) {
      nodes { id title }
    }
  }
}
"""

QUERY_FIND_ARCH_ISSUE = """
query FindArchitectureIssue($projectId: ID!, $needle: String!) {
  issues(
    filter: {
      project: { id: { eq: $projectId } }
      title: { containsIgnoreCase: $needle }
    }
    first: 20
  ) {
    nodes { id identifier title }
  }
}
"""

MUTATION_DOCUMENT_CREATE = """
mutation DocumentCreate($input: DocumentCreateInput!) {
  documentCreate(input: $input) {
    success
    document { id title }
  }
}
"""

def load_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: str, data: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def graphql_request(api_key: str, query: str, variables: Dict[str, Any]) -> Dict[str, Any]:
    body = json.dumps({"query": query, "variables": variables}).encode("utf-8")
    req = urllib.request.Request(
        "https://api.linear.app/graphql",
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": api_key,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        print(f"HTTP Error {e.code}: {e.reason}", file=sys.stderr)
        print(e.read().decode("utf-8"), file=sys.stderr)
        raise


def resolve_project_id(api_key: str, project_id: Optional[str], project_name: Optional[str]) -> Optional[Dict[str, str]]:
    if project_id:
        return {"id": project_id, "name": project_name or ""}

    if not project_name:
        return None

    resp = graphql_request(api_key, QUERY_PROJECTS, {"first": 250})
    if resp.get("errors"):
        raise RuntimeError("Could not list projects: " + json.dumps(resp["errors"]))

    nodes = ((resp.get("data") or {}).get("projects") or {}).get("nodes") or []
    # case-insensitive exact match first, then contains match
    lname = project_name.strip().lower()
    for p in nodes:
        if (p.get("name") or "").strip().lower() == lname:
            return {"id": p.get("id"), "name": p.get("name")}

    for p in nodes:
        if lname in ((p.get("name") or "").lower()):
            return {"id": p.get("id"), "name": p.get("name")}

    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--export", default="./input-output-data/parent_issue_export.json", help="Path to parent_issue_export.json")
    ap.add_argument("--project-id", default=None, help="Linear project UUID (optional if parent issue has a project)")
    ap.add_argument("--project-name", default=None, help="Project name to resolve to an id (optional)")
    ap.add_argument("--doc-title", default="architecture.md", help="Exact document title to search for or create")
    ap.add_argument("--issue-needle", default="Architecture", help="Search needle for finding an existing fallback architecture issue")
    ap.add_argument("--architecture-file", default=None, help="Path to architecture.md to insert into Linear if missing")
    ap.add_argument("--dry-run", action="store_true", help="Do not create; only report")
    ap.add_argument("--out", default="./input-output-data/architecture_report.json", help="Where to write the report JSON")
    args = ap.parse_args()

    api_key = os.environ.get("LINEAR_API_KEY", "").strip()
    if not api_key:
        print("ERROR: LINEAR_API_KEY is not set.")
        return 2

    export_data = load_json(args.export)
    parent_issue_id = (export_data.get("meta") or {}).get("parentIssueId")
    if not parent_issue_id:
        print("ERROR: export.meta.parentIssueId is missing. Run export_parent_issue.sh first.")
        return 2

    # Load parent issue context (team + project)
    ctx_resp = graphql_request(api_key, QUERY_PARENT_CONTEXT, {"id": parent_issue_id})
    if ctx_resp.get("errors"):
        print("ERROR: Linear API returned errors while fetching parent issue context:")
        print(json.dumps(ctx_resp["errors"], indent=2))
        return 1

    issue = (ctx_resp.get("data") or {}).get("issue") or {}
    team = issue.get("team") or {}
    project = issue.get("project") or {}

    team_id = team.get("id")
    if not team_id:
        print("ERROR: Could not determine teamId from parent issue.")
        return 1

    inferred_project_id = project.get("id")
    inferred_project_name = project.get("name")

    project_info = None
    if args.project_id or args.project_name:
        project_info = resolve_project_id(api_key, args.project_id, args.project_name)
        if not project_info:
            print("ERROR: Could not resolve project from provided --project-id/--project-name.")
            return 1
    elif inferred_project_id:
        project_info = {"id": inferred_project_id, "name": inferred_project_name or ""}
    else:
        print("ERROR: Parent issue has no project, and no --project-id/--project-name was provided.")
        print("Hint: provide --project-name 'My Project' or --project-id <uuid>.")
        return 2

    project_id = project_info["id"]
    project_name = project_info.get("name") or ""

    report: Dict[str, Any] = {
        "meta": {
            "parentIssueId": parent_issue_id,
            "parentIssueIdentifier": issue.get("identifier"),
            "team": {"id": team.get("id"), "key": team.get("key"), "name": team.get("name")},
            "project": {"id": project_id, "name": project_name},
            "docTitle": args.doc_title,
            "dryRun": bool(args.dry_run),
        },
        "found": None,
        "foundType": None, # "document" or "issue"
        "created": None,
        "action": None,
        "notes": [],
    }

    # 1. Search for Document (Priority)
    find_doc = graphql_request(api_key, QUERY_FIND_ARCH_DOC, {"projectId": project_id, "title": args.doc_title})
    if find_doc.get("errors"):
        print("ERROR: Linear API returned errors while searching for architecture document:")
        print(json.dumps(find_doc["errors"], indent=2))
        return 1
    
    doc_nodes = ((find_doc.get("data") or {}).get("project") or {}).get("documents", {}).get("nodes") or []
    if doc_nodes:
        existing = doc_nodes[0]
        report["found"] = existing
        report["foundType"] = "document"
        report["action"] = "found"
        report["notes"].append(f"Architecture defined in Project Document: '{existing.get('title')}'")
        save_json(args.out, report)
        print(f"Found architecture document: {existing.get('title','')} (ID: {existing.get('id','')})")
        return 0

    # 2. Search for Issue (Fallback)
    find_issue = graphql_request(api_key, QUERY_FIND_ARCH_ISSUE, {"projectId": project_id, "needle": args.issue_needle})
    if find_issue.get("errors"):
        print("ERROR: Linear API returned errors while searching for architecture issue:")
        print(json.dumps(find_issue["errors"], indent=2))
        return 1

    issue_nodes = ((find_issue.get("data") or {}).get("issues") or {}).get("nodes") or []
    if issue_nodes:
        existing = issue_nodes[0]
        report["found"] = existing
        report["foundType"] = "issue"
        report["action"] = "found_legacy"
        report["notes"].append(f"Architecture defined in Issue (legacy): {existing.get('identifier')} {existing.get('title')}")
        save_json(args.out, report)
        print(f"Found architecture issue (legacy): {existing.get('identifier','')} — {existing.get('title','')}")
        return 0

    # 3. Missing - Create Document
    if args.dry_run:
        report["action"] = "missing_dry_run"
        report["notes"].append("Architecture definition is missing (dry-run). Provide --architecture-file to create a Project Document.")
        save_json(args.out, report)
        print("Architecture definition is missing (dry-run). Provide --architecture-file to create a [Project Document].")
        return 2

    if not args.architecture_file:
        report["action"] = "missing_no_file"
        report["notes"].append("Architecture definition is missing. No --architecture-file provided.")
        save_json(args.out, report)
        print("Architecture definition is missing.")
        print("Provide --architecture-file ./architecture.md to create a Project Document.")
        return 2

    # Create from file
    with open(args.architecture_file, "r", encoding="utf-8") as f:
        arch_body = f.read().strip()

    if not arch_body:
        print("ERROR: architecture file is empty.")
        return 2

    input_obj: Dict[str, Any] = {
        "projectId": project_id,
        "title": args.doc_title,
        "content": arch_body,
        # "icon": "box" # optional
    }

    # Retry a bit on transient failures
    last_err = None
    for attempt in range(4):
        try:
            out = graphql_request(api_key, MUTATION_DOCUMENT_CREATE, {"input": input_obj})
            if out.get("errors"):
                last_err = json.dumps(out["errors"])
                time.sleep(0.8 * (attempt + 1))
                continue
            payload = (out.get("data") or {}).get("documentCreate") or {}
            if not payload.get("success"):
                last_err = "Mutation returned success=false"
                time.sleep(0.8 * (attempt + 1))
                continue
            created = payload.get("document")
            report["created"] = created
            report["action"] = "created"
            report["foundType"] = "document"
            report["notes"].append("Architecture Project Document created from architecture file.")
            save_json(args.out, report)
            print(f"Created architecture document: {created.get('title','')} (ID: {created.get('id','')})")
            return 0
        except Exception as e:
            last_err = str(e)
            time.sleep(0.8 * (attempt + 1))

    report["action"] = "create_failed"
    report["notes"].append(f"Create document failed: {last_err}")
    save_json(args.out, report)
    print("ERROR: Failed to create architecture document.")
    if last_err:
        print(last_err)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
