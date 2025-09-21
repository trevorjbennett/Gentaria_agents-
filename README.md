# Gentaria Agent System

This repository is the single source of truth for Gentaria's JSON-first agent operations. It packages the authoritative specification in `agent.md`, JSON schemas, seed data, and helper tooling so IDE agents such as Codex can plan, execute, and log work directly against the versioned `json.db`.

## What's in the repo
- `agent.md` – comprehensive playbook covering agent roles, orchestration loop, guardrails, and operating procedures.
- `schemas/` – JSON Schema definitions (`*.schema.json`) that govern objectives, projects, tasks, runs, policies, and routing tables.
- `data/` – seed `json.db` entries (`*.jsonl` logs + configs) that bootstraps objectives, projects, policies, routing, and pricing information.
- `scripts/validate.py` – validation helper that enforces schema compliance across the datastore.
- `Makefile` – convenience targets (`make validate`, `make test`, `make fmt`) for validation, testing, and formatting.
- `setup manual.md` – step-by-step guide for wiring Codex/VS Code into the workflow.
- `artifacts/`, `agents/`, `policies/`, `tests/` – placeholders for generated outputs, agent implementations, policy modules, and automated checks.

## Getting started
1. Ensure Python 3 is available and install dependencies: `pip install jsonschema pytest`.
2. Validate that seeded data conforms to the schemas: `make validate` (runs `python scripts/validate.py`).
3. Format JSON files as needed with `make fmt` (requires Prettier in your PATH).
4. When tests are added under `tests/`, run them with `make test`.

## Operating model overview
- Agents read and write exclusively through the JSON files in `data/`, treating them as the shared datastore (`json.db`).
- Every task update and execution run should comply with the published schemas to maintain traceability and replayability.
- Outputs such as reports, code, or analyses live under `artifacts/` using the path conventions described in `agent.md`.

Refer to `setup manual.md` for detailed Codex integration steps and `agent.md` for the full governance and orchestration specification.
