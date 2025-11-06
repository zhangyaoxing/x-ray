.PHONY: all clean deps build test install dist init lint format check-lint

# Project name
PROJECT_NAME = x-ray

# Python interpreter (using Python from virtual environment)
PYTHON = .venv/bin/python

# Default target
all: deps build

# Install dependencies
deps:
	@echo "Creating virtual environment..."
	python3 -m venv .venv
	@echo "Installing dependencies..."
	$(PYTHON) -m pip install -r requirements.txt
	@echo "Activate virtual environment: \033[33msource .venv/bin/activate\033[0m"

# Build executable (default to lightweight build)
build: build-lite

# Build executable without AI support (lightweight)
build-lite:
	@echo "Building lightweight executable (without AI support)..."
	$(PYTHON) -m PyInstaller --onefile --name $(PROJECT_NAME) \
		--add-data="templates:templates" \
		--add-data="config.json:." \
		--add-data="libs:libs" \
		--add-data="compatibility_matrix.json:." \
		--hidden-import=openai \
		--exclude-module torch \
		--exclude-module torchvision \
		--exclude-module transformers \
		--exclude-module numpy \
		--exclude-module scipy \
		x-ray
	@echo "\033[32m✓ Lightweight build complete: dist/x-ray\033[0m"

# Build executable with AI support (includes torch, transformers)
build-ai:
	@echo "Building full executable (with AI support)..."
	$(PYTHON) -m PyInstaller --onefile --name $(PROJECT_NAME)-ai \
		--add-data="templates:templates" \
		--add-data="config.json:." \
		--add-data="libs:libs" \
		--add-data="compatibility_matrix.json:." \
		--hidden-import torch \
		--hidden-import transformers \
		--hidden-import transformers.models.qwen2 \
		--hidden-import tokenizers \
		x-ray
	@echo "\033[32m✓ Full build complete: dist/x-ray-ai\033[0m"
	@echo "\033[33m⚠ Note: This does NOT include model weights. Models will be downloaded on first use.\033[0m"

# Run tests 
test:
	@echo "Running tests..."
	$(PYTHON) -m pytest tests/ -v
	@echo "\033[32m✓ All tests passed!\033[0m"

# Run pylint
lint:
	@echo "Running pylint..."
	$(PYTHON) -m pylint libs/ x-ray --rcfile=.pylintrc
	@echo "\033[32m✓ Linting complete!\033[0m"

# Run pylint and show only errors
check-lint:
	@echo "Running pylint (errors only)..."
	$(PYTHON) -m pylint libs/ x-ray --rcfile=.pylintrc --errors-only
	@echo "\033[32m✓ No errors found!\033[0m"

# Format code with black
format:
	@echo "Formatting code with black..."
	$(PYTHON) -m black libs/ x-ray tests/ --line-length=120
	@echo "\033[32m✓ Code formatted!\033[0m"

# Check formatting without making changes
format-check:
	@echo "Checking code format..."
	$(PYTHON) -m black libs/ x-ray tests/ --line-length=120 --check
	@echo "\033[32m✓ Code format is correct!\033[0m"

# Run all quality checks
check: format-check lint test
	@echo "\033[32m✓ All checks passed!\033[0m"
	
# Clean build artifacts
clean:
	@echo "Cleaning build artifacts..."
	rm -rf build/ dist/ __pycache__/
	# Only remove spec file if it exists
	[ -f $(PROJECT_NAME).spec ] && rm $(PROJECT_NAME).spec || true
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Help information
help:
	@echo "X-Ray Project Makefile"
	@echo ""
	@echo "Available commands:"
	@echo "  make deps         - Install all dependencies including virtual environment setup"
	@echo "  make build        - Build executable (default: lightweight version without AI)"
	@echo "  make build-lite   - Build lightweight executable without AI support (~15MB)"
	@echo "  make build-ai     - *Experimental* Build full executable with AI libraries (~2GB, models downloaded separately)"
	@echo "  make check        - Run all tests"
	@echo "  make lint         - Run pylint on code"
	@echo "  make check-lint   - Run pylint (errors only)"
	@echo "  make format       - Format code with black"
	@echo "  make format-check - Check code formatting without changes"
	@echo "  make qa           - Run all quality checks (format + lint + test)"
	@echo "  make clean        - Clean build artifacts"
	@echo "  make all          - Install dependencies and build executable"
	@echo "  make help         - Display this help information"
	@echo ""
	@echo "Build modes:"
	@echo "  build-lite: Excludes torch/transformers (recommended for distribution)"
	@echo "  build-ai:   Includes AI libraries but NOT model weights (downloaded on first use)"
	@echo ""
	@echo "Quality checks:"
	@echo "  make lint         - Full pylint analysis with warnings"
	@echo "  make check-lint   - Quick check (errors only)"
	@echo "  make format       - Auto-format code"
	@echo "  make qa           - Run all checks (recommended before commit)"
	@echo ""
	@echo "Examples:"
	@echo "  make deps       - First-time setup in a new environment"
	@echo "  make build      - Build without AI (recommended for distribution)"
	@echo "  make build-ai   - Build with AI support (for local AI analysis)"
	@echo "  make qa         - Run all quality checks before committing"
	@echo "  make clean      - Clean build artifacts"
