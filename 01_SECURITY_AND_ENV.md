# 01_SECURITY_AND_ENV.md

## Secrets Policy (non-negotiable)
- NEVER paste or store `LINEAR_API_KEY` in chat logs, patch JSON, export JSON, or repo files.
- `LINEAR_API_KEY` must remain in your local shell environment only.

## Your Environment Variable Setup (Already Done)
You have already stored:
- `LINEAR_API_KEY` in `~/.zshrc`

### Required per-session step (terminal)
Run:
source ~/.zshrc

Then verify:
echo "$LINEAR_API_KEY"

If it prints nothing, stop and fix that before continuing.

## Minimal Shell Environment Notes
Some tools/agents restrict environment variable access. In other contexts you mentioned using:
include_only = ["PATH", "HOME", "LINEAR_API_KEY"]

This Groombot assumes you run the scripts locally in your shell, so they will read `LINEAR_API_KEY` from the environment after you `source ~/.zshrc`.

## Linear GraphQL API
Endpoint:
https://api.linear.app/graphql

All requests must include:
Authorization: <LINEAR_API_KEY>
Content-Type: application/json

## Local Dependencies
- `bash`
- `curl`
- `python3`
- Optional but recommended: `jq` (for pretty JSON output)

## Script executability reminder
After editing scripts, re-run:
chmod +x ./scripts/init_cache.sh
chmod +x ./scripts/export_parent_issue.sh
chmod +x ./scripts/apply_patch.py
chmod +x ./scripts/ensure_architecture_issue.py

No dependencies should ever require embedding your API key into files.