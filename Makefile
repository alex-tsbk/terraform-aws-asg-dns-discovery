.EXPORT_ALL_VARIABLES:

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
	if exist .\\.git\\hooks then rmdir .\\.git\\hooks /q /s fi
	if exist .\\$(VENV)\\ ( rmdir .\\.venv /q /s )
	if exist poetry.lock ( del poetry.lock /q /s )