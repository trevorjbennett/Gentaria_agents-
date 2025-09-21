.PHONY: validate test fmt

validate:
	python scripts/validate.py

test:
	pytest -q

fmt:
	prettier -w data/*.json data/*.jsonl || true
