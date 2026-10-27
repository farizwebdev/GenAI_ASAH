.PHONY: install test lint format run train validate-data clean

install:
	pip install -r requirements.txt

test:
	pytest -q

train:
	python -m app.training.train_intent

tune:
	python -m app.training.augment_and_tune

report:
	python -m app.training.evaluate

train-matcher:
	python -m app.training.train_matcher

evaluate-extractor:
	python -m app.training.evaluate_extractor

validate-data:
	python scripts/validate_data.py

lint:
	ruff check .

format:
	ruff format .

run:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
