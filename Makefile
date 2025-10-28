.PHONY: all clean deps build test install dist init

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
	@echo "Activate virtual environment: \033[33msource .venv/bin/activate\033[0m"
	@echo "Installing dependencies..."
	$(PYTHON) -m pip install -r requirements.txt

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
		--exclude-module torch \
		--exclude-module torchvision \
		--exclude-module transformers \
		--exclude-module numpy \
		--exclude-module scipy \
		x-ray
	@echo "✓ Lightweight build complete: dist/x-ray (~11MB)"

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
	@echo "✓ Full build complete: dist/x-ray-ai (~2GB+)"
	@echo "⚠ Note: This does NOT include model weights. Models will be downloaded on first use."

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
	@echo "  make deps       - Install all dependencies including virtual environment setup"
	@echo "  make build      - Build executable (default: lightweight version without AI)"
	@echo "  make build-lite - Build lightweight executable without AI support (~15MB)"
	@echo "  make build-ai   - *Experimental* Build full executable with AI libraries (~2GB, models downloaded separately)"
	@echo "  make clean      - Clean build artifacts"
	@echo "  make all        - Install dependencies and build executable"
	@echo "  make help       - Display this help information"
	@echo ""
	@echo "Build modes:"
	@echo "  build-lite: Excludes torch/transformers (recommended for distribution)"
	@echo "  build-ai:   Includes AI libraries but NOT model weights (downloaded on first use)"
	@echo ""
	@echo "Examples:"
	@echo "  make deps       - First-time setup in a new environment"
	@echo "  make build      - Build without AI (recommended for distribution)"
	@echo "  make build-ai   - Build with AI support (for local AI analysis)"
	@echo "  make clean      - Clean build artifacts"
