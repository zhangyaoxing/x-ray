.PHONY: all clean deps build test install dist init

# Project name
PROJECT_NAME = x-ray

# Python interpreter (using Python from virtual environment)
PYTHON = .venv/bin/python

# Default target
all: deps build

# Initialize project in a new environment
init:
	@echo "Initializing project in a new environment..."
	@echo "Creating virtual environment..."
	python3 -m venv .venv
	@echo "Installing dependencies..."
	.venv/bin/pip install -r requirements.txt
	@echo "Project initialized successfully! Activate the virtual environment with: source .venv/bin/activate"

# Install dependencies
deps:
	@echo "Installing dependencies..."
	$(PYTHON) -m pip install -r requirements.txt

# Build executable
build:
	@echo "Building executable..."
	@if [ ! -f x-ray.spec ]; then \
		echo "Creating spec file since it does not exist..."; \
		$(PYTHON) -m PyInstaller --onefile --name $(PROJECT_NAME) \
			--add-data="templates:templates" \
			--add-data="config.json:." \
			--add-data="libs:libs" \
			--add-data="compatibility_matrix.json:." \
			x-ray; \
	else \
		$(PYTHON) -m PyInstaller x-ray.spec; \
	fi

# Clean build artifacts
clean:
	@echo "Cleaning build artifacts..."
	rm -rf build/ dist/ __pycache__/
	# Only remove spec file if it exists
	[ -f $(PROJECT_NAME).spec ] && rm $(PROJECT_NAME).spec || true
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Create virtual environment
venv:
	@echo "Creating virtual environment..."
	python3 -m venv .venv
	@echo "Activate virtual environment: source .venv/bin/activate"

# Run tests (if any)
test:
	@echo "Running tests..."
	# Uncomment the next line if tests are available
	# $(PYTHON) -m pytest tests/

# Create distribution package
dist: build
	@echo "Creating distribution package..."
	mkdir -p dist/package
	cp dist/$(PROJECT_NAME) dist/package/
	cp -r templates dist/package/
	cp config.json dist/package/
	cp README.md dist/package/
	cd dist && tar -czf $(PROJECT_NAME)-package.tar.gz package
	@echo "Distribution package created: dist/$(PROJECT_NAME)-package.tar.gz"

# Help information
help:
	@echo "X-Ray Project Makefile"
	@echo ""
	@echo "Available commands:"
	@echo "  make init     - Initialize project in a new environment (create venv and install dependencies)"
	@echo "  make deps     - Install all dependencies"
	@echo "  make build    - Build executable"
	@echo "  make clean    - Clean build artifacts"
	@echo "  make all      - Install dependencies and build executable"
	@echo "  make venv     - Create virtual environment"
	@echo "  make test     - Run tests (if any)"
	@echo "  make dist     - Create complete distribution package"
	@echo "  make help     - Display this help information"
	@echo ""
	@echo "Examples:"
	@echo "  make init     - First-time setup in a new environment"
	@echo "  make          - Default operation (install dependencies and build)"
	@echo "  make clean    - Clean build artifacts"
	@echo "  make dist     - Create distribution package"
