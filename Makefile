.PHONY: run
run:
	@echo "Running the script..."
	@python -m src.main

.PHONY: uv-run
uv-run:
	@echo "Running the script..."
	@uv run -m src.main

