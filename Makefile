.PHONY: all clean deps build test install dist init lint format check-lint flake8

# Project name
PROJECT_NAME = x-ray

# Detect OS and set Python path accordingly
ifeq ($(OS),Windows_NT)
	PYTHON = .venv\Scripts\python.exe
	VENV_ACTIVATE = .venv\Scripts\activate
	RM = cmd /C rmdir /S /Q
	MKDIR = cmd /C mkdir
else
	PYTHON = .venv/bin/python
	VENV_ACTIVATE = source .venv/bin/activate
	RM = rm -rf
	MKDIR = mkdir -p
endif

# Default target
all: deps build test

# Install dependencies
deps:
	@echo "Creating virtual environment..."
	python -m venv .venv
	@echo "Installing dependencies..."
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -r requirements-base.txt
	@echo "Activate virtual environment: $(VENV_ACTIVATE)"

# Install AI dependencies (for build-ai)
deps-ai:
	@echo "Creating virtual environment..."
	python -m venv .venv
	@echo "Installing AI dependencies..."
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -r requirements-ai.txt
	@echo "Activate virtual environment: $(VENV_ACTIVATE)"

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
	$(PYTHON) -m pytest
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

# Run flake8 for syntax errors
flake8:
	@echo "Running flake8 (syntax errors only)..."
	$(PYTHON) -m flake8 libs/ x-ray --select=E9,F63,F7,F82 --show-source --statistics
	@echo "\033[32m✓ No syntax errors!\033[0m"

# Format code with black
format:
	@echo "Formatting code with black..."
	$(PYTHON) -m black libs/ x-ray tests/
	@echo "\033[32m✓ Code formatted!\033[0m"

# Check formatting without making changes
check-format:
	@echo "Checking code format..."
	$(PYTHON) -m black libs/ x-ray tests/ --check
	@echo "\033[32m✓ Code format is correct!\033[0m"

# Run all quality checks
check: check-format check-lint flake8 test
	@echo "\033[32m✓ All checks passed!\033[0m"

# Clean build artifacts
clean:
	@echo "Cleaning build artifacts..."
ifeq ($(OS),Windows_NT)
	@if exist build $(RM) build
	@if exist dist $(RM) dist
	@if exist __pycache__ $(RM) __pycache__
	@if exist $(PROJECT_NAME).spec del /F $(PROJECT_NAME).spec
	@for /d /r %%i in (__pycache__) do @if exist "%%i" $(RM) "%%i"
	@for /d /r %%i in (*.egg-info) do @if exist "%%i" $(RM) "%%i"
	@del /S /Q *.pyc 2>nul || exit 0
else
	rm -rf build/ dist/ __pycache__/
	[ -f $(PROJECT_NAME).spec ] && rm $(PROJECT_NAME).spec || true
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
endif

# Help information
help:
	@echo "X-Ray Project Makefile"
	@echo ""
	@echo "Available commands:"
	@echo "  make deps         - Install all dependencies including virtual environment setup"
	@echo "  make build        - Build executable (default: lightweight version without AI)"
	@echo "  make build-lite   - Build lightweight executable without AI support (~15MB)"
	@echo "  make build-ai     - *Experimental* Build full executable with AI libraries (~2GB, models downloaded separately)"
	@echo "  make test         - Run all tests"
	@echo "  make lint         - Run pylint on code"
	@echo "  make check-lint   - Run pylint (errors only)"
	@echo "  make flake8       - Run flake8 (syntax errors only)"
	@echo "  make format       - Format code with black"
	@echo "  make check-format - Check code formatting without changes"
	@echo "  make check        - Run all quality checks (format + lint + flake8 + test)"
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
	@echo "  make flake8       - Flake8 syntax error check"
	@echo "  make format       - Auto-format code"
	@echo "  make check        - Run all checks (recommended before commit)"
	@echo ""
	@echo "Examples:"
	@echo "  make deps       - First-time setup in a new environment"
	@echo "  make build      - Build without AI (recommended for distribution)"
	@echo "  make build-ai   - Build with AI support (for local AI analysis)"
	@echo "  make check      - Run all quality checks before committing"
	@echo "  make clean      - Clean build artifacts"
