import glob
import json
import sys
from jsonschema import Draft202012Validator as V


def load_schema(name: str):
    with open(f"schemas/{name}.schema.json", "r", encoding="utf-8") as f:
        return json.load(f)


def check(file_glob: str, schema: str) -> bool:
    ok = True
    schema_obj = load_schema(schema)
    validator = V(schema_obj)
    for path in glob.glob(file_glob):
        if path.endswith(".jsonl"):
            with open(path, "r", encoding="utf-8") as f:
                for i, line in enumerate(f, 1):
                    if not line.strip():
                        continue
                    obj = json.loads(line)
                    errors = sorted(validator.iter_errors(obj), key=lambda e: e.path)
                    for error in errors:
                        ok = False
                        print(f"[{path}:{i}] {error.message}")
        else:
            with open(path, "r", encoding="utf-8") as f:
                obj = json.load(f)
            errors = sorted(validator.iter_errors(obj), key=lambda e: e.path)
            for error in errors:
                ok = False
                print(f"[{path}] {error.message}")
    return ok


ok = True
ok &= check("data/objectives.jsonl", "objective")
ok &= check("data/projects.jsonl", "project")
ok &= check("data/tasks.jsonl", "task")
ok &= check("data/runs.jsonl", "run")
ok &= check("data/policies.jsonl", "policy")
ok &= check("data/routing.json", "routing")

sys.exit(0 if ok else 1)
