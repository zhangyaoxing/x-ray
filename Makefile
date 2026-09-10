.DEFAULT_GOAL := build
.PHONY: build clean deps plugin-deps test unit-test cluster-setup cluster-teardown integration-test integration-test-deps lint minify help

# Project name
PROJECT_NAME = x-ray

# MongoDB binary used to start the test cluster (full-test / integration-test).
MONGOD ?= $(shell command -v mongod)
# Cluster topology created by prepare_cluster.sh: "rs" (replica set) or "sh" (sharded cluster).
TYPE ?= rs
# MongoDB major.minor series to test in integration-test (the latest installed patch of each).
VERSIONS ?= 6.0 7.0 8.0

# Detect OS and set Python path accordingly
ifeq ($(OS),Windows_NT)
	# Use forward slashes to be compatible with Git Bash and cmd
	PYTHON = .venv/Scripts/python.exe
	VENV_ACTIVATE = .venv/Scripts/activate
	RM = cmd /C rmdir /S /Q
	MKDIR = cmd /C mkdir
	DELIMITER = ;
else
	PYTHON = .venv/bin/python
	VENV_ACTIVATE = source .venv/bin/activate
	RM = rm -rf
	MKDIR = mkdir -p
	DELIMITER = :
endif

# Install dependencies
deps:
	@echo "Creating virtual environment..."
	python3 -m venv .venv
	@echo "Installing dependencies from pyproject.toml..."
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -e ".[dev]" --config-settings editable_mode=compat
	@echo "Activate virtual environment: $(VENV_ACTIVATE)"

# Install the plugins that ship with the binary. The PyInstaller hook bundles
# every mongo-x-ray-* plugin installed in the venv, so in a fresh release
# environment (which has exactly these) the binary contains log + ftdc + hc
# and nothing else.
#
# mongo-x-ray-hc is installed from source as well, even though the binary does
# not expose it as a command: log depends on it, and the 2.0.0 release on PyPI
# still does `from mongo_x_ray.issues import ...`, a module core 2.1.0 no longer
# provides. Installing an older hc would break plugin discovery (and the frozen
# binary). Switch this line to `mongo-x-ray-hc>=2.1.0` once hc 2.1.0 is on PyPI.
plugin-deps:
	@echo "Installing the bundled plugins (mongo-x-ray-log, mongo-x-ray-ftdc, mongo-x-ray-hc)..."
	$(PYTHON) -m pip install \
		mongo-x-ray-log@git+https://github.com/zhangyaoxing/mongo-x-ray-log.git@main \
		mongo-x-ray-ftdc@git+https://github.com/zhangyaoxing/mongo-x-ray-ftdc.git@main \
		mongo-x-ray-hc@git+https://github.com/zhangyaoxing/mongo-x-ray-hc.git@main
	@echo "\033[32m✓ Bundled plugins installed\033[0m"

# Build executable
build:
	@echo "Building executable..."
	$(PYTHON) -m PyInstaller --onefile --name $(PROJECT_NAME) \
		--add-data="src/mongo_x_ray/templates$(DELIMITER)mongo_x_ray/templates" \
		--add-data="src/mongo_x_ray/config.json$(DELIMITER)mongo_x_ray" \
		--add-data="src/mongo_x_ray/compatibility_matrix.json$(DELIMITER)mongo_x_ray" \
		--additional-hooks-dir=hooks \
		--icon="misc/x-ray.ico" \
		src/mongo_x_ray/__main__.py
	@echo "\033[32m✓ Build complete: dist/x-ray\033[0m"

# Run unit tests in the core and in every local plugin checkout under plugins/.
unit-test:
	@echo "Running core unit tests..."
	$(PYTHON) -m pytest -m "not integration"
	@echo "\033[32m✓ Core unit tests passed!\033[0m"
	@if [ -d plugins ]; then \
		for d in plugins/*; do \
			if [ -d "$$d" ] && [ -f "$$d/Makefile" ]; then \
				echo "=== unit-test: $$d ==="; \
				$(MAKE) -C "$$d" unit-test || exit 1; \
			fi; \
		done; \
	fi

# Alias matching the core convention.
test: unit-test

# Prepare the test cluster: stop any existing cluster, start a fresh replica
# set, seed it, and generate the getMongoData report.
cluster-setup:
	@echo "Stopping any existing test cluster..."
	@if [ -d .tests/mongo ]; then (cd .tests/mongo && mlaunch kill --signal 9) 2>/dev/null || true; sleep 3; rm -rf .tests/mongo; fi
	@echo "Starting MongoDB cluster ($(TYPE))..."
	bash tests/prepare_cluster.sh $(MONGOD) $(TYPE)
	@echo "Generating getMongoData report..."
	mongosh --quiet mongodb://localhost:47017 misc/getMongoData.js > .tests/mongo/getMongoData-output.json
	@echo "Copying FTDC samples to stable paths..."
	@MONGOD_FTDC="$$(find .tests/mongo -path '*db/diagnostic.data*' -name 'metrics.*' -not -name '*.interim' -not -name '*.tmp' | head -1)"; \
		if [ -n "$$MONGOD_FTDC" ]; then cp "$$MONGOD_FTDC" .tests/mongo/metrics.mongod; else echo "WARNING: no finalized mongod FTDC file found" >&2; fi; \
		MONGOS_FTDC="$$(find .tests/mongo -path '*mongos.diagnostic.data*' -name 'metrics.*' -not -name '*.interim' -not -name '*.tmp' | head -1)"; \
		if [ -n "$$MONGOS_FTDC" ]; then cp "$$MONGOS_FTDC" .tests/mongo/metrics.mongos; fi

# Tear down the test cluster: kill its processes and remove its files.
cluster-teardown:
	@echo "Stopping the test cluster..."
	@(cd .tests/mongo 2>/dev/null && mlaunch kill --signal 9) || true
	@rm -rf .tests

# Verify the tools required by integration-test (mtools, m, mongosh).
integration-test-deps:
	@for tool in mlaunch m mongosh; do \
		if ! command -v $$tool >/dev/null 2>&1; then \
			echo "Error: '$$tool' is required by integration-test but was not found in PATH" >&2; \
			exit 1; \
		fi; \
	done
	@echo "✓ integration-test dependencies found"

# Test the integration suite against the latest installed patch of every
# MongoDB series listed in VERSIONS, with both rs and sh topologies.
integration-test: integration-test-deps
	@for version in $(VERSIONS); do \
		patch="$$(m installed | awk '{print $$NF}' | grep -E "^$$version\\." | sort -V | tail -1)"; \
		if [ -z "$$patch" ]; then echo "Error: no installed MongoDB $$version.x (run 'm $$version')" >&2; exit 1; fi; \
		for type in rs sh; do \
			echo "=== MongoDB $$patch ($$type) ==="; \
			make cluster-setup MONGOD="$$(m bin $$patch)" TYPE="$$type" || { make cluster-teardown; exit 1; }; \
			HC_URI="mongodb://localhost:47017" \
				GMD_SAMPLE="$(CURDIR)/.tests/mongo/getMongoData-output.json" \
				GMD_TOPOLOGY="$$type" \
				LOG_SAMPLE="$$(mongod_log="$$(find "$(CURDIR)/.tests/mongo" -name 'mongod.log' | head -1)"; mongos_log="$$(find "$(CURDIR)/.tests/mongo" -name 'mongos.log' | head -1)"; if [ -n "$$mongos_log" ]; then echo "$$mongos_log:$$mongod_log"; else echo "$$mongod_log"; fi)" \
				FTDC_SAMPLE="$$(s="$(CURDIR)/.tests/mongo/metrics.mongod"; [ -f "$(CURDIR)/.tests/mongo/metrics.mongos" ] && s="$(CURDIR)/.tests/mongo/metrics.mongos:$$s"; echo "$$s")" \
				$(PYTHON) -m pytest -m "integration"; \
				status=$$?; \
				make cluster-teardown; \
				if [ $$status -ne 0 ]; then echo "FAILED: MongoDB $$version ($$type)" >&2; exit $$status; fi; \
		done; \
	done
	@echo "\033[32m✓ All integration tests passed!\033[0m"

# Run ruff lint and format checks (the shared lint contract)
lint:
	@echo "Running ruff check..."
	$(PYTHON) -m ruff check src tests
	@echo "Running ruff format check..."
	$(PYTHON) -m ruff format --check src tests
	@echo "\033[32m✓ No lint errors found!\033[0m"

# Minify templates in the core and in every local plugin checkout under plugins/.
minify:
	@echo "Minifying templates..."
	cd src/mongo_x_ray/templates && ./minify.sh
	@echo "\033[32m✓ Templates minified!\033[0m"
	@if [ -d plugins ]; then \
		for d in plugins/*; do \
			if [ -d "$$d" ] && [ -f "$$d/Makefile" ]; then \
				echo "=== minify: $$d ==="; \
				$(MAKE) -C "$$d" minify || exit 1; \
			fi; \
		done; \
	fi

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
	@echo "  make deps         - Install dev dependencies declared in pyproject.toml"
	@echo "  make plugin-deps  - Install the bundled plugins (log, ftdc) for the build"
	@echo "  make build        - Build executable (bundles log + ftdc plugins)"
	@echo "  make minify       - Minify HTML/JS templates (core + plugins/)"
	@echo "  make unit-test    - Run unit tests (core + plugins/)"
	@echo "  make test         - Alias for unit-test"
	@echo "  make cluster-setup - Start and seed a test cluster"
	@echo "  make cluster-teardown - Stop and clean up a test cluster"
	@echo "  make integration-test - Test all installed MongoDB versions (rs + sh)"
	@echo "  make lint         - Run ruff check and ruff format check"
	@echo "  make clean        - Clean build artifacts"
	@echo "  make help         - Display this help information"
