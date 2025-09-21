# Gentaria Agent System — Codex Setup Manual

This guide walks you through configuring Visual Studio Code with an OpenAI Codex–style assistant (or any compatible GitHub Copilot / OpenAI API automation) so the agent can read and write directly to the Gentaria `json.db` and follow the operating guardrails defined in `agent.md`.

## 1. Prerequisites

1. **Local tooling**
   - Python 3.10+
   - `pipx` or `pip` (for dependencies)
   - `make`
   - Node.js 18+ (for Prettier if you plan to run `make fmt`)
2. **VS Code extensions**
   - *Official OpenAI* or *GitHub Copilot / Copilot Labs* extension that exposes a Chat/Codex interface capable of running commands.
   - *Python* extension (for linting + virtualenv helpers).
3. **OpenAI API access** (or Copilot subscription) with model permissions for code generation.

> 💡 Keep your API key in the standard VS Code secrets store or environment variable (`OPENAI_API_KEY`). Never check the key into git.

## 2. Clone and Bootstrap the Repo

```bash
git clone <your-fork-url> gentaria
cd gentaria
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt  # optional; repo currently depends only on jsonschema & pytest
pip install jsonschema pytest
make validate
```

If `requirements.txt` is absent, `pip install jsonschema pytest` is sufficient for validation.

## 3. Prepare VS Code Workspace

1. Open the folder in VS Code: `code gentaria`.
2. Accept the workspace recommendation to use the virtual environment (`.venv`).
3. Ensure the `Makefile` tasks are available (`Terminal → Run Task… → make validate`).
4. Create a **`.env`** file (ignored by git) with environment variables you want Codex to inherit, e.g.:

   ```env
   OPENAI_API_KEY=sk-...
   GENTARIA_COST_CAP=5
   ```

## 4. Configure the Codex Prompt Template

Codex should be guided using the structure defined in Section 9 of `agent.md`:

- Declare role, goal, input schema, output schema.
- Echo cost cap & risk tier from the task object (`data/tasks.jsonl`).
- End with: `Return only JSON conforming to <schema>`.

Create a reusable snippet (e.g., VS Code *User Snippets* or Copilot *Prompt Library*) similar to:

```text
Role: {agent_role} for Gentaria.
Goal: {task_title}
Context: See agent.md guardrails.
Input schema: {schema_name}
Output schema: {schema_name}
Cost cap: £{cost_cap}
Risk tier: {risk_tier}
Policies: Refer to data/policies.jsonl.

Return only JSON conforming to {schema_name}.
```

## 5. Workflow: Letting Codex “Take” a Task

1. **Pick a task** from `data/tasks.jsonl` whose `assignee` matches the agent persona you plan to run.
2. **Lock the task** for Codex by updating its `status` to `"doing"` (or create a branch/commit note explaining the session). You can edit manually or prompt Codex to issue the update.
3. **Provide context** to Codex:
   - Paste the selected task JSON.
   - Include related project/objective records from `data/projects.jsonl` and `data/objectives.jsonl`.
   - Reference policies in `data/policies.jsonl` and guardrails in `agent.md`.
4. **Prompt Codex** with the template above and specify expected artifacts (e.g., Markdown path under `artifacts/`).
5. **Review Codex output** to ensure it:
   - Matches the schema (validate with `python scripts/validate.py --file ...` if you add flags, or run `make validate`).
   - Appends artifacts to the correct path.
   - Updates `data/tasks.jsonl` (status to `review` or `done`, fill `artifacts`).
6. **Log the run** by appending a `run.v1` entry to `data/runs.jsonl` with timestamps, cost, outputs, and citations.

## 6. Recommended Automation Helpers

- **VS Code Tasks**: add `.vscode/tasks.json` entries for `make validate`, `make fmt`, and `pytest` so Codex can execute them via `task <name>` commands.
- **Command Palette scripts**: create shell snippets like `./scripts/new_task.py` to mint IDs. Codex can run these via the integrated terminal.
- **JSON validation**: install *Even Better TOML* or *JSON Schema* VS Code extension to associate the schemas in `/schemas` with the data files for inline validation.

## 7. Verification Before Commit

1. Run `make validate` and ensure exit code `0`.
2. If you modified or generated code/tests, run `make test` (currently executes `pytest -q`).
3. Run `make fmt` if JSON formatting drifts (requires Prettier globally or in the repo).
4. Stage changes and commit with conventional messages, e.g.:

   ```bash
   git add data/tasks.jsonl data/runs.jsonl artifacts/... 
   git commit -m "builder: update task tsk-001 output"
   ```

## 8. Appendix — Troubleshooting

| Issue | Fix |
| --- | --- |
| `jsonschema` ModuleNotFoundError | Activate `.venv`, run `pip install jsonschema pytest`. |
| Validation errors referencing `task.v1` | Ensure each JSON object matches the schema, with required fields present and enums respected. |
| Codex tries to write invalid JSON | Add explicit reminder in the prompt: *"Return only valid JSON conforming to task.v1; do not include prose."* |
| Git conflicts in `data/*.jsonl` | Use append-only discipline; avoid reordering lines. Resolve by rebasing and re-running Codex if necessary. |

---

With this setup, Codex can operate as a first-class agent inside the Gentaria workflow, keeping all state inside the Git-tracked `json.db` and following the governance described in `agent.md`.
