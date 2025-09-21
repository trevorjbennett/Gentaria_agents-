# Gentaria Agent System — Authoritative Spec (agent.md)

> Purpose: make AI agents the **Single Source of Truth (SLT)** for planning, execution, and reporting across Gentaria, with all state persisted in a lightweight **`json.db`** (JSON/JSONL files versioned in git). This doc is designed to be pasted into your repo as `agent.md`, and paired with the seed files and schemas below.

---

## 0) Core Principles

* **SLT by design**: Agents never act on ad-hoc memory; they read+write only through `json.db`.
* **Human-in-the-loop (HITL) where it matters**: Autonomy for low-risk, fast review for medium risk, explicit approval for high risk.
* **Frugality**: System must operate within **£300/month**. Budget is enforced in policy.
* **Traceability**: Every decision yields a signed record: inputs, options, chosen path, expected ROI, outcome, cost.
* **Composability**: Agents are small, specialized workers connected as a graph; orchestration is declarative.
* **Deterministic IO**: Inputs and outputs are explicit JSON structures validated by JSON Schema.
* **Reproducibility**: Any run can be replayed from `runs.jsonl` + artifacts.

---

## 1) Agent Roles (Agent Graph)

Each agent is a stateless function from **(goal, context, policies)** to **(plan/tasks or artifacts)**, logging to `runs.jsonl`.

* **Orchestrator**

  * Reads objectives, routes to projects/agents, enforces policy, schedules tasks, aggregates results.
* **Planner (PM)**

  * Decomposes objectives → projects → epics → tasks; defines acceptance criteria and cost caps.
* **Researcher**

  * Searches internal docs (Drive connector), extracts facts, writes citations and notes.
* **Builder**

  * Generates code, IaC, data pipelines, docs; emits diffs and test plans.
* **Analyst**

  * Creates dashboards, cost/ROI models (FinOps), A/B analyses, KPI rollups.
* **Sales**

  * Prospecting, outreach templates, CRM updates, proposal drafts.
* **Support**

  * Vendor onboarding playbooks (CoralHub), user responses, FAQ updates.
* **FinOps**

  * Budget guardrails, anomaly detection, vendor SKUs, monthly close report.
* **Risk & Compliance**

  * Classifies data, flags PII, gates high-risk actions, maintains audit trail.
* **Memory**

  * Summarizes long threads, maintains embeddings/indices (refs only; no secrets).

Each agent **reads** from: `/data/*.jsonl` + project artifacts.
Each agent **writes** to: `/data/tasks.jsonl`, `/data/runs.jsonl`, `/artifacts/*`.

---

## 2) Repositories & File Layout

```
/agents/                 (code for agents; one dir per agent)
/schemas/                (JSON Schemas)
/data/                   (json.db; JSON/JSONL files)
/artifacts/              (outputs: md, csv, images, code diffs)
/policies/               (optional policy modules)
/scripts/                (CLI helpers)
/tests/                  (unit tests & golden runs)
agent.md                 (this document)
Makefile                 (validation, test, lint)
```

---

## 3) Data Contracts (Schemas)

> Place these in `/schemas`. Use AJV or Python `jsonschema` to validate.

### 3.1 Objective

`/schemas/objective.schema.json`

```json
{
  "$id": "objective.v1",
  "type": "object",
  "required": ["id", "title", "owner", "kpis", "deadline", "priority", "status"],
  "properties": {
    "id": {"type":"string"},
    "title": {"type":"string"},
    "description": {"type":"string"},
    "owner": {"type":"string"},
    "priority": {"type":"string","enum":["P0","P1","P2"]},
    "deadline": {"type":"string","format":"date"},
    "kpis": {"type":"array","items":{"type":"string"}},
    "status": {"type":"string","enum":["planned","active","blocked","done"]},
    "links": {"type":"array","items":{"type":"string"}}
  },
  "additionalProperties": false
}
```

### 3.2 Project

`/schemas/project.schema.json`

```json
{
  "$id": "project.v1",
  "type": "object",
  "required": ["id","name","domain","owner","stage","risk","budget_monthly","guardrails","slas"],
  "properties": {
    "id":{"type":"string"},
    "name":{"type":"string"},
    "domain":{"type":"string","enum":["vantis","coralhub","palm","viridion","predicta","baypay"]},
    "description":{"type":"string"},
    "owner":{"type":"string"},
    "stage":{"type":"string","enum":["idea","mvp","pilot","ga","paused"]},
    "risk":{"type":"string","enum":["low","med","high"]},
    "budget_monthly":{"type":"number","minimum":0},
    "guardrails":{"type":"array","items":{"type":"string"}},
    "slas":{"type":"object","properties":{
      "latency_ms":{"type":"number"},
      "cost_ceiling_gbp":{"type":"number"},
      "error_rate_target":{"type":"number"}
    }},
    "kpis":{"type":"array","items":{"type":"string"}},
    "data_access":{"type":"array","items":{"type":"string"}},
    "hitl_required":{"type":"boolean"}
  },
  "additionalProperties": false
}
```

### 3.3 Task

`/schemas/task.schema.json`

```json
{
  "$id": "task.v1",
  "type":"object",
  "required":["id","project_id","title","assignee","tooling","cost_cap_gbp","risk_tier","status"],
  "properties":{
    "id":{"type":"string"},
    "project_id":{"type":"string"},
    "title":{"type":"string"},
    "details":{"type":"string"},
    "assignee":{"type":"string","enum":["orchestrator","planner","researcher","builder","analyst","sales","support","finops","risk","memory"]},
    "tooling":{"type":"array","items":{"type":"string"}},
    "risk_tier":{"type":"string","enum":["A","B","C"]},
    "cost_cap_gbp":{"type":"number","minimum":0},
    "status":{"type":"string","enum":["todo","doing","review","done","blocked"]},
    "artifacts":{"type":"array","items":{"type":"string"}},
    "acceptance":{"type":"array","items":{"type":"string"}}
  },
  "additionalProperties": false
}
```

### 3.4 Run (Execution Log)

`/schemas/run.schema.json`

```json
{
  "$id":"run.v1",
  "type":"object",
  "required":["id","task_id","agent","started_at","ended_at","cost_gbp","status"],
  "properties":{
    "id":{"type":"string"},
    "task_id":{"type":"string"},
    "agent":{"type":"string"},
    "started_at":{"type":"string","format":"date-time"},
    "ended_at":{"type":"string","format":"date-time"},
    "inputs":{"type":"object"},
    "outputs":{"type":"object"},
    "cost_gbp":{"type":"number","minimum":0},
    "status":{"type":"string","enum":["ok","error","skipped"]},
    "notes":{"type":"string"},
    "citations":{"type":"array","items":{"type":"string"}}
  },
  "additionalProperties": false
}
```

### 3.5 Policy

`/schemas/policy.schema.json`

```json
{
  "$id":"policy.v1",
  "type":"object",
  "required":["id","name","rules"],
  "properties":{
    "id":{"type":"string"},
    "name":{"type":"string"},
    "rules":{"type":"array","items":{
      "type":"object",
      "required":["when","then"],
      "properties":{
        "when":{"type":"object"},
        "then":{"type":"object"}
      }
    }}
  },
  "additionalProperties": false
}
```

### 3.6 Routing

`/schemas/routing.schema.json`

```json
{
  "$id":"routing.v1",
  "type":"object",
  "required":["goal_to_projects","project_to_agents"],
  "properties":{
    "goal_to_projects":{"type":"array","items":{
      "type":"object",
      "required":["goal_regex","projects"],
      "properties":{
        "goal_regex":{"type":"string"},
        "projects":{"type":"array","items":{"type":"string"}}
      }
    }},
    "project_to_agents":{"type":"object","additionalProperties":{
      "type":"array","items":{"type":"string"}
    }}
  },
  "additionalProperties": false
}
```

---

## 4) Seed json.db (Initial Data)

> Place these under `/data`. Use JSONL for append-only logs, JSON for static config.

### 4.1 Objectives

`/data/objectives.jsonl`

```json
{"id":"obj-001","title":"Hit £1k MRR in 90 days","description":"Do it via Vantis consulting + CoralHub commissions","owner":"founder","priority":"P0","deadline":"2025-12-20","kpis":["MRR>=1000","CAC<£50","MoM>20%"],"status":"active","links":[]}
```

### 4.2 Projects

`/data/projects.jsonl`

```json
{"id":"prj-vantis","name":"Vantis Edge (FinOps)","domain":"vantis","description":"Cloud spend audits + Vantis Score + playbooks","owner":"founder","stage":"mvp","risk":"low","budget_monthly":75,"guardrails":["read-only creds","no prod mutations"],"slas":{"latency_ms":0,"cost_ceiling_gbp":150,"error_rate_target":0.01},"kpis":["#audits","£saved","MRR"],"data_access":["drive:gentaria/vantis"],"hitl_required":false}
{"id":"prj-coralhub","name":"CoralHub MVP","domain":"coralhub","description":"Local services marketplace (iOS)","owner":"founder","stage":"mvp","risk":"med","budget_monthly":125,"guardrails":["email rate<=3/day","payments via PSP only"],"slas":{"latency_ms":300,"cost_ceiling_gbp":125,"error_rate_target":0.05},"kpis":["GMV","take_rate","active_vendors"],"data_access":["drive:gentaria/coralhub"],"hitl_required":true}
{"id":"prj-viridion","name":"Viridion (Hydrogen Intel)","domain":"viridion","description":"Pivot to research/data products: LCOH, policy scan","owner":"founder","stage":"idea","risk":"med","budget_monthly":50,"guardrails":["no hardware spend","no lab ops"],"slas":{"latency_ms":0,"cost_ceiling_gbp":50,"error_rate_target":0.02},"kpis":["reports_sold","newsletter_subs"],"data_access":["drive:gentaria/energy"],"hitl_required":true}
```

### 4.3 Tasks

`/data/tasks.jsonl`

```json
{"id":"tsk-001","project_id":"prj-vantis","title":"Create FinOps audit template + score","details":"Checklist + scoring JSON + sample report","assignee":"planner","tooling":["drive","markdown"],"risk_tier":"A","cost_cap_gbp":0,"status":"doing","artifacts":[],"acceptance":["score.json created","report.md created"]}
{"id":"tsk-002","project_id":"prj-vantis","title":"Prospect 50 startups with high AWS/GCP spend","details":"Find 50 leads, enrich contacts, draft outreach","assignee":"sales","tooling":["sheets","email"],"risk_tier":"B","cost_cap_gbp":5,"status":"todo","artifacts":[],"acceptance":["50 leads CSV","email template v1"]}
{"id":"tsk-003","project_id":"prj-coralhub","title":"Vendor onboarding playbook","details":"5 pilot vendors; listing form; T&Cs","assignee":"support","tooling":["docs","forms"],"risk_tier":"B","cost_cap_gbp":0,"status":"todo","artifacts":[],"acceptance":["playbook.md","form link","T&Cs.md"]}
{"id":"tsk-004","project_id":"prj-viridion","title":"Hydrogen LCOH calculator v0","details":"Inputs: CAPEX proxy, solar LCOE, SOEC efficiency; outputs: £/kg","assignee":"analyst","tooling":["python","sheets"],"risk_tier":"A","cost_cap_gbp":0,"status":"todo","artifacts":[],"acceptance":["lcoh.py","examples.csv"]}
```

### 4.4 Policies

`/data/policies.jsonl`

```json
{"id":"pol-budget","name":"Budget guardrails","rules":[
  {"when":{"run.cost_gbp":{">":25}},"then":{"action":"require_approval","by":"finops"}},
  {"when":{"month.cost_total":{">=":250}},"then":{"action":"alert","to":"founder"}},
  {"when":{"month.cost_total":{">=":300}},"then":{"action":"halt","scope":"noncritical"}}
]}
{"id":"pol-risk","name":"Risk routing","rules":[
  {"when":{"task.risk_tier":"A"},"then":{"action":"auto_execute"}},
  {"when":{"task.risk_tier":"B"},"then":{"action":"review","by":"owner"}},
  {"when":{"task.risk_tier":"C"},"then":{"action":"escalate","to":"founder"}}
]}
{"id":"pol-data","name":"Data access","rules":[
  {"when":{"resource.classification":"restricted"},"then":{"action":"deny"}},
  {"when":{"resource.classification":"confidential"},"then":{"action":"mask_fields","fields":["email","name","iban"]}}
]}
```

### 4.5 Pricelist (Costs)

`/data/pricelist.json`

```json
{
  "month_budget_gbp": 300,
  "items": {
    "openai_api_token":"0-50 pay-as-you-go",
    "firebase_free_tier":"0",
    "email_sender":"10",
    "domain_dns":"10",
    "misc_tools_buffer":"30"
  }
}
```

### 4.6 Routing

`/data/routing.json`

```json
{
  "goal_to_projects": [
    {"goal_regex":"(?i)\\bMRR\\b|revenue|£1k","projects":["prj-vantis","prj-coralhub"]},
    {"goal_regex":"(?i)hydrogen|energy","projects":["prj-viridion"]}
  ],
  "project_to_agents": {
    "prj-vantis":["planner","sales","analyst","finops"],
    "prj-coralhub":["planner","builder","support","analyst"],
    "prj-viridion":["researcher","analyst"]
  }
}
```

### 4.7 Runs (empty to start)

`/data/runs.jsonl`

```json
```

---

## 5) Orchestration Loop (Pseudo)

```python
def route_objective(objective, routing):
  projs = []
  for rule in routing["goal_to_projects"]:
    if re.search(rule["goal_regex"], objective["title"] + " " + objective.get("description","")):
      projs.extend(rule["projects"])
  return list(dict.fromkeys(projs))  # dedupe

def decide_risk_action(task, policies, month_cost_total, run_cost):
  # evaluate pol-risk, pol-budget in order
  # returns one of: "auto_execute", "review", "escalate", "halt"
  ...

def orchestrate():
  objective = pick_active_objective()
  routing = load_json("data/routing.json")
  projects = route_objective(objective, routing)

  plan = planner_decompose(objective, projects)          # writes tasks.jsonl
  for task in plan.tasks:
    action = decide_risk_action(task, policies, month_cost_total(), 0)
    if action == "halt": continue
    if action == "auto_execute":
      run = execute_agent(task.assignee, task)
    elif action == "review":
      request_review(task)
      continue
    elif action == "escalate":
      escalate(task)
      continue
    log_run(run)                                         # append to runs.jsonl
  aggregate_metrics_and_propose_improvements()
```

---

## 6) Guardrails & Safety

* **Budget**

  * Soft alert at £250/month; hard stop at £300 for noncritical tasks.
  * Per-task default cost cap: £5; Planner can raise to £25 with reason.
* **Data**

  * No raw secrets in `json.db`. Use references to a local/CI secret store.
  * Classification required for any new artifact (`public|internal|confidential|restricted`).
* **Risk**

  * Autonomous only for Tier A (low risk, reversible, ≤£10).
  * Tier B requires review; Tier C requires explicit approval.
* **Banned actions**

  * Trading, real payments, outbound user emails at scale, legal/medical advice.
* **Logging**

  * Every run must include: inputs summary, outputs summary, cost, citations, confidence.

---

## 7) IO Conventions

* **All reads/writes are JSON or JSONL**. One JSON object per line for logs.
* **IDs** are `prefix-uuid` (e.g., `tsk-<nano-id>`).
* **Timestamps** in ISO 8601 with timezone (UTC).
* **Artifacts** go under `/artifacts/<project>/<yyyy-mm>/<slug>.<ext>`.
* **Citations** use stable URIs or internal Drive URLs.

---

## 8) Local Tooling

### 8.1 Makefile

```
.PHONY: validate test fmt

validate:
python scripts/validate.py

test:
pytest -q

fmt:
prettier -w data/*.json data/*.jsonl || true
```

### 8.2 `scripts/validate.py` (sketch)

```python
import json, glob, sys
from jsonschema import validate, Draft202012Validator as V

def load_schema(name):
    with open(f"schemas/{name}.schema.json") as f: return json.load(f)

def check(file_glob, schema):
    ok = True
    sch = load_schema(schema)
    for path in glob.glob(file_glob):
        if path.endswith(".jsonl"):
            with open(path) as f:
                for i,line in enumerate(f,1):
                    if not line.strip(): continue
                    obj = json.loads(line)
                    errs = sorted(V(sch).iter_errors(obj), key=lambda e: e.path)
                    for e in errs:
                        ok=False
                        print(f"[{path}:{i}] {e.message}")
        else:
            obj = json.load(open(path))
            errs = sorted(V(sch).iter_errors(obj), key=lambda e: e.path)
            for e in errs:
                ok=False
                print(f"[{path}] {e.message}")
    return ok

ok = True
ok &= check("data/objectives.jsonl","objective")
ok &= check("data/projects.jsonl","project")
ok &= check("data/tasks.jsonl","task")
ok &= check("data/runs.jsonl","run")
ok &= check("data/policies.jsonl","policy")
ok &= check("data/routing.json","routing")

sys.exit(0 if ok else 1)
```

---

## 9) Prompts (Codex/LLM Adapters)

All agent prompts must:

* Declare **role**, **goal**, **inputs schema**, **output schema**, **policies**.
* Echo back **cost cap** and **risk tier**.
* End with: “**Return only JSON** conforming to `<schema>`.”

**Planner prompt (example):**

```
Role: Planner agent for Gentaria.
Goal: Decompose objective into tasks under these projects: <list>.
Constraints: budget cap £300/mo; per-task default cap £5 unless reasoned raise; risk tier A only for reversible, low-cost.
Input: objective (objective.v1), projects (project.v1[])
Output: array of tasks (task.v1[]) with acceptance criteria.

Return only JSONL (one task per line), valid task.v1.
```

**Sales prompt (example):**

```
Role: Sales agent. Create 50 startup leads with likely high cloud spend; produce CSV fields: company, url, contact_name, contact_email, reason.
Constraints: zero paid data sources. Risk tier B (review). Cost cap £5.
Output: artifacts/leads.csv + task update to status='review'.
Return only JSON object { "artifacts": ["artifacts/vantis/2025-09/leads.csv"], "notes": "..."}.
```

---

## 10) QA & Evals

* **Task success metrics**: completion rate, time to complete, cost per task, review pass rate.
* **Model evals (where applicable)**: unit tests for codegen; factuality checks for research.
* **Weekly retro**: Analyst aggregates `runs.jsonl` → `/artifacts/weekly/retro-YYYY-MM-DD.md` with:

  * KPI delta vs. targets
  * Top blockers
  * Budget usage summary
  * Proposed policy changes (as PR snippets)

---

## 11) Change Management

* Changes to `agent.md` or any `/schemas/*.json` → PR with:

  * Rationale
  * Migration notes for `/data/*.jsonl`
  * Updated tests
* Schema versioning: use `$id` suffix (`objective.v1`, `objective.v1.1`).
* Provide `scripts/migrate_<from>_to_<to>.py` for non-backward-compatible changes.

---

## 12) Minimal Getting-Started Script

`/scripts/new_task.py` (sketch)

```python
import json, uuid, datetime as dt
import sys
tid = "tsk-" + uuid.uuid4().hex[:8]
task = {
  "id": tid,
  "project_id": sys.argv[1],
  "title": "CHANGEME",
  "details": "",
  "assignee": "planner",
  "tooling": ["drive"],
  "risk_tier": "A",
  "cost_cap_gbp": 0,
  "status": "todo",
  "artifacts": [],
  "acceptance": []
}
print(json.dumps(task))
```

Append output to `data/tasks.jsonl`:

```
python scripts/new_task.py prj-vantis >> data/tasks.jsonl
```

---

## 13) Extension Packs (Later)

* **CRM**: `/data/crm.jsonl` with contacts/leads schema.
* **Calendaring**: `/data/calendar.jsonl` for meetings.
* **Embeddings**: `/data/index/*` store vector IDs only; raw text remains in Drive.

---

## 14) Concrete First Week Plan (Solo, £300/mo)

* Planner creates tasks to:

  * Draft **Vantis FinOps audit** template + Vantis Score JSON.
  * Build **lead list** (50 startups) and **outreach template**.
  * Define **CoralHub vendor onboarding** flow (5 pilot vendors).
  * Build **Viridion LCOH v0** (pure software model; no hardware).
* FinOps sets budget policy and alerts.
* Orchestrator runs daily: route objective → create/review tasks → execute A-tier tasks.

---

# Appendix A — Agent Implementation Notes

* Agents can be implemented as small scripts (Python/Node) that:

  * Load schemas; validate input JSON.
  * Read `data/*.jsonl`, filter for their scope.
  * Produce outputs and append `runs.jsonl`.
  * Write artifacts under `/artifacts/...`.
* Each agent binary accepts:

  * `--task-id`, `--input-json`, `--cost-cap`.
* Orchestrator simply invokes agent binaries per task with a runner that:

  * Wraps with cost/time accounting.
  * Applies policies before/after execution.

---

# Appendix B — Testing

* **Golden runs**: store exemplar `runs.jsonl` entries under `/tests/golden/`.
* **Unit tests** assert:

  * Schema conformance.
  * Planner emits acceptance criteria.
  * Budget policy triggers at soft/hard thresholds.
  * Risk routing enforces HITL.

---

# Appendix C — Viridion “Lean” Modeling Spec

* Artifact: `/artifacts/viridion/lcoh/lcoh.py`
* Inputs (CSV): `capex_proxy`, `lcoe_solar`, `soec_efficiency`, `utilization`, `o&m`, `lifetime_years`
* Outputs: `lcoh_gbp_per_kg`, `sensitivity` (tornado chart data)
* Analyst agent writes a short report: `/artifacts/viridion/lcoh/report.md`

---

## Done-for-you Seed Files

If you want them bundled, use the **seed JSON** above for `/data/*` and the **schemas** under `/schemas/*`. Add the Makefile and `scripts/validate.py`. This gives you a working SLT skeleton that Codex (or your build scripts) can extend immediately.
