.EXPORT_ALL_VARIABLES:
SUBDIR_ROOTS := src/lambda
DIRS := . $(shell find $(SUBDIR_ROOTS) -type d)
GARBAGE_PATTERNS := .pytest_cache
GARBAGE := $(foreach DIR,$(DIRS),$(addprefix $(DIR)/,$(GARBAGE_PATTERNS)))

VENV = .venv


setup: venv install

.PHONY: venv
venv:
	@echo "Creating .venv..."
	poetry env use python3

.PHONY: install
install:
	@echo "Installing dependencies..."
	poetry install

.PHONY: format
format:
	@echo "Sorting imports, formatting code..."
	isort --profile black -l $(PYTHON_MAX_LINE_LENGTH) src/
	black -l $(PYTHON_MAX_LINE_LENGTH) src/

.PHONY: clean
clean:
	rm -rf $(GARBAGE)