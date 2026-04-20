install:
	pip install -e ".[dev]"

test:
	pytest

lint:
	ruff check src tests

format:
	ruff check --fix src tests

run:
	streamlit run src/weather_dashboard/app.py
