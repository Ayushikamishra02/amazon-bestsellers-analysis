.PHONY: help setup report sql test lint app notebook all clean

PY ?= python

help:        ## show this help
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-10s\033[0m %s\n", $$1, $$2}'

setup:       ## install dependencies + the package (editable)
	$(PY) -m pip install -r requirements-dev.txt
	$(PY) -m pip install -e .

report:      ## regenerate all figures, tables and reports/findings.md
	$(PY) -m bestsellers.report

sql:         ## run every SQL query with DuckDB
	$(PY) -m bestsellers.sql

test:        ## run the test suite
	$(PY) -m pytest

lint:        ## static checks
	ruff check src app tests

app:         ## launch the interactive dashboard
	streamlit run app/streamlit_app.py

notebook:    ## re-execute the analysis notebook
	jupyter nbconvert --to notebook --execute --inplace notebooks/bestsellers_analysis.ipynb

all: lint test report notebook  ## everything CI does, plus outputs

clean:       ## remove caches
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	rm -rf .pytest_cache .ruff_cache
