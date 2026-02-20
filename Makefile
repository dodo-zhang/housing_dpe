.PHONY: fmt lint test run all clean

fmt:
	uv run ruff format .

lint:
	uv run ruff check .

test:
	uv run pytest -q

run:
	uv run python -m housing_dpe.cli --config config/params.yaml --outdir outputs

all: fmt lint test run

clean:
	rm -rf outputs