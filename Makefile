.PHONY: fmt lint test run outputs paper view clean clean_outputs clean_paper all

# -----------------------
# Python quality targets
# -----------------------
fmt:
	uv run ruff format .

lint:
	uv run ruff check .

test:
	uv run pytest -q

# -----------------------
# Run pipeline (produces outputs/)
# -----------------------
run:
	uv run python -m housing_dpe.cli --config config/params.yaml

# alias: explicit naming
outputs: run

# -----------------------
# LaTeX (paper) targets
# -----------------------
LATEX_DIR := latex
LATEX_MAIN := main.tex
LATEX_OUT := build

paper: outputs
	cd $(LATEX_DIR) && latexmk -pdf -synctex=1 -interaction=nonstopmode -file-line-error -outdir=$(LATEX_OUT) $(LATEX_MAIN)

# optional: open pdf in VS Code viewer if LaTeX Workshop is installed
# (this uses VS Code command line; harmless if it doesn't work)
view:
	code -r $(LATEX_DIR)/$(LATEX_OUT)/main.pdf || true

# -----------------------
# Clean targets
# -----------------------
clean_outputs:
	rm -rf outputs

clean_paper:
	cd $(LATEX_DIR) && latexmk -c -outdir=$(LATEX_OUT) $(LATEX_MAIN) || true
	rm -rf $(LATEX_DIR)/$(LATEX_OUT)

clean: clean_outputs clean_paper

# -----------------------
# "All" = code quality + run pipeline + compile paper
# -----------------------
all: fmt lint test paper