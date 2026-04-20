install:
	pip install -e ".[dev]"

test:
	pytest

lint:
	ruff check src tests

format:
	ruff check --fix src tests

run:
	weather-comparison-engine build-sample-dashboard
