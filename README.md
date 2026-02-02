<img width="600" height="600" alt="image" src="https://github.com/user-attachments/assets/e5bb79bf-08e7-4e14-8f7b-edb8a910e4be" />

Groombot exists to make Linear issues “model-ready” before you hand them off to a high-cost coding model like OpenAI Codex, Anthropic Claude, Google Gemini, or similar. Those models can burn expensive credits quickly when requirements are vague, tickets are underspecified, or scope is blurred. The goal here is to front-load clarity so implementation time is spent writing code—not asking basic questions.

The workflow uses a conversational chatbot to groom a single parent issue end-to-end: normalize titles, define crisp acceptance criteria, identify dependencies/unknowns, propose estimates, and produce a strictly-scoped patch back to Linear. By doing the “thinking and shaping” work with lower-cost interaction, you reduce churn, minimize rework, and maximize the value of every paid token/credit when you eventually switch to an implementation-focused model.

- A strict, single parent issue grooming workflow for Linear using ChatGPT as the guided operator.

This repo contains:
	•	authoritative workflow documentation
	•	scripts to export parent issue data from Linear
	•	scripts to apply a patch back to Linear (dry-run supported)
	•	a ready-to-paste grooming_prompt.md for a fresh ChatGPT Desktop session

⸻

More technically, what this tool does

For exactly one parent issue per session, this workflow:
	1.	Exports the parent issue + sub-issues from Linear into parent_issue_export.json
	2.	Guides grooming one sub-issue at a time
	3.	Produces groom_patch.json (only real IDs, only intended changes)
	4.	Optionally applies the patch back to Linear and generates apply_report.json

⸻

Requirements

	•	macOS / Linux (or WSL)
	•	python3 (recommended 3.10+)
	•	curl
	•	A Linear API key with permission to read and (optionally) update issues

⸻

First time setup

Linear API key (local environment only)
1.	Create a Linear API key in Linear.
2.	Add it to your shell profile (example for zsh):
``` bash
echo 'export LINEAR_API_KEY="PASTE_YOUR_KEY_HERE"' >> ~/.zshrc
source ~/.zshrc
```
3.	Confirm it’s available:
``` bash
echo "$LINEAR_API_KEY"
```
If that prints blank, fix your shell setup before continuing.
⸻

Initialize local folders and permissions

From the repo root:
``` bash
source ~/.zshrc
chmod +x ./scripts/init_cache.sh
chmod +x ./scripts/export_parent_issue.sh
chmod +x ./scripts/apply_patch.py
./scripts/init_cache.sh
```
This ensures:
	•	local-cache/ exists and contains empty cache JSON files (if not already present)
	•	input-output-data/ exists
⸻

Usage (ChatGPT Desktop workflow)

1) Zip the entire contents of the repo folder for upload to chatgpt-desktop

2) Start a fresh session
	1.	Open ChatGPT Desktop
	2.	Create a new chat
	3.	Copy the entire contents of grooming_prompt.md
	4.	Paste it as the first message in that chat

3) Follow the agent instructions

The agent will instruct you to:
	•	export fresh data with export_parent_issue.sh
	•	upload input-output-data/parent_issue_export.json
	•	groom one sub-issue at a time
	•	produce input-output-data/groom_patch.json
	•	if a split is confirmed, include createSubIssues in groom_patch.json and run scripts/create_sub_issues.py (see 06_CREATE_SUB_ISSUES.md)

## Architecture anchor issue
Groombot expects each Linear project to have a single top-level **Architecture Definition** issue. If it cannot be found, the operator should provide an `architecture.md` file so Groombot can create it (or provide the file each run). See `07_ARCHITECTURE_ANCHOR.md`.
