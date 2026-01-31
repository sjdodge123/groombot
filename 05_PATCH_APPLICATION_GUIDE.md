## Scripted Usage (Recommended)

### One-time setup (or after updating scripts)
1) Load your env var:
source ~/.zshrc

2) Ensure scripts are executable (re-run anytime scripts change):
chmod +x ./scripts/init_cache.sh
chmod +x ./scripts/export_epic.sh
chmod +x ./scripts/apply_patch.py

3) Initialize cache (safe to run repeatedly):
./scripts/init_cache.sh

### Per-epic flow
1) Export current epic state:
./scripts/export_epic.sh <EPIC_IDENTIFIER>

This writes:
- ./input-output-data/epic_export.json

2) Upload `./input-output-data/epic_export.json` to the chat agent and groom.
Agent outputs:
- groom_patch.json

3) Apply patch + update cache:
python3 ./scripts/apply_patch.py --patch ./input-output-data/groom_patch.json --export ./input-output-data/epic_export.json

This writes:
- ./input-output-data/apply_report.json
And if everything succeeds, it updates:
- ./local-cache/groomed_epics.json
- ./local-cache/groomed_issues.json

### Dry run (preview only)
python3 ./scripts/apply_patch.py --patch ./input-output-data/groom_patch.json --export ./input-output-data/epic_export.json --dry-run