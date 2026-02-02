## Scripted Usage (Recommended)


## Pre-flight: architecture anchor
After exporting the parent issue, and before applying patches or creating new issues, ensure the project has an **Architecture Definition** issue (or the operator has provided `architecture.md` for this run).
See `07_ARCHITECTURE_ANCHOR.md`.

### One-time setup (or after updating scripts)
1) Load your env var:
source ~/.zshrc

2) Ensure scripts are executable (re-run anytime scripts change):
chmod +x ./scripts/init_cache.sh
chmod +x ./scripts/export_parent_issue.sh
chmod +x ./scripts/apply_patch.py

3) Initialize cache (safe to run repeatedly):
./scripts/init_cache.sh

### Per-parent issue flow
1) Export current parent issue state:
./scripts/export_parent_issue.sh <PARENT_ISSUE_IDENTIFIER>

This writes:
- ./input-output-data/parent_issue_export.json

2) Upload `./input-output-data/parent_issue_export.json` to the chat agent and groom.
Agent outputs:
- groom_patch.json

2.5) (Optional) Create new sub-issues when a split is confirmed
If `groom_patch.json` includes `createSubIssues`, create them before applying updates:

```bash
python3 ./scripts/create_sub_issues.py   --patch ./input-output-data/groom_patch.json   --export ./input-output-data/parent_issue_export.json   --dry-run
```

Then run without `--dry-run` to create for real:

```bash
python3 ./scripts/create_sub_issues.py   --patch ./input-output-data/groom_patch.json   --export ./input-output-data/parent_issue_export.json
```

This writes:
- ./input-output-data/create_report.json


3) Apply patch + update cache:
python3 ./scripts/apply_patch.py --patch ./input-output-data/groom_patch.json --export ./input-output-data/parent_issue_export.json

This writes:
- ./input-output-data/apply_report.json
And if everything succeeds, it updates:
- ./local-cache/groomed_parent_issues.json
- ./local-cache/groomed_issues.json

### Dry run (preview only)
python3 ./scripts/apply_patch.py --patch ./input-output-data/groom_patch.json --export ./input-output-data/parent_issue_export.json --dry-run