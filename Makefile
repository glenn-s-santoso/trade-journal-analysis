.PHONY: install run uv-run clean dev-setup pre-commit

install:
	@echo "Installing the package..."
	@pip install -e .

dev-setup:
	@echo "Setting up development environment..."
	@pip install -e ".[dev]"

run:
	@echo "Running the script..."
	@python -m src.main

uv-run:
	@echo "Running the script with uv..."
	@uv run -m src.main

clean:
	@echo "Cleaning up build artifacts..."
	@rm -rf build/ dist/ *.egg-info/ __pycache__/ .pytest_cache/
	@find . -name "__pycache__" -type d -exec rm -rf {} +
	@find . -name "*.pyc" -delete
	@find . -name "*.pyo" -delete
	@find . -name "*.pyd" -delete

pre-commit:
	@echo "Setting up pre-commit hooks..."
	@pre-commit install

pre-commit-run:
	@echo "Running pre-commit on all files..."
	@pre-commit run --all-files

