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

evaluate-rag:
	python -m app.training.evaluate_rag

evaluate-guardrails:
	python -m app.training.evaluate_guardrails

train-sentiment:
	python -m app.training.train_sentiment

validate-data:
	python scripts/validate_data.py

lint:
	ruff check .

format:
	ruff format .

run:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

docker-build:
	docker build -t sabana-genai-service:latest .

docker-run:
	docker run -d -p 8000:8000 --env-file .env --name sabana-genai sabana-genai-service:latest

warmup:
	python scripts/warmup.py

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
