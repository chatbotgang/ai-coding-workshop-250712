# AI Coding Workshop Setup
SHELL := /bin/bash
PYTHON_VERSION := 3.12.7
VENV_NAME := ai-coding-workshop
PROJECT_DIR := $(shell pwd)

.PHONY: init help clean lint get-shell-rc setup-pyenv-shell setup-pyenv-virtualenv-shell setup-poetry-shell reload-shell-config restart-shell

# Default target
help:
	@echo "Available targets:"
	@echo "  init          - Initialize development environment"
	@echo "  restart-shell - Restart/reload shell configuration" 
	@echo "  clean         - Clean up virtual environment"
	@echo "  lint          - Run code linting (black, isort, pyright)"
	@echo "  help          - Show this help message"

# Initialize development environment
init:
	@echo "🚀 Initializing development environment..."
	@$(MAKE) check-install-pyenv
	@$(MAKE) check-install-pyenv-virtualenv
	@$(MAKE) create-virtualenv
	@$(MAKE) set-default-virtualenv
	@$(MAKE) check-install-poetry
	@$(MAKE) install-dependencies
	@$(MAKE) reload-shell-config
	@echo "✅ Development environment initialized successfully!"
	@echo "💡 Shell configuration has been automatically updated and reloaded!"
	@echo "🎯 If you want to restart your shell completely, run: make restart-shell"

# Check and install pyenv
check-install-pyenv:
	@echo "🔍 Checking pyenv installation..."
	@if ! command -v pyenv &> /dev/null; then \
		echo "📦 Installing pyenv..."; \
		if [[ "$(shell uname)" == "Darwin" ]]; then \
			if command -v brew &> /dev/null; then \
				echo "🔧 Installing Python build dependencies..."; \
				HOMEBREW_NO_AUTO_UPDATE=1 brew install openssl readline sqlite3 xz zlib tcl-tk@8 libb2; \
				echo "📦 Installing pyenv..."; \
				brew install pyenv; \
			else \
				echo "❌ Homebrew not found. Please install Homebrew first."; \
				exit 1; \
			fi; \
		else \
			curl https://pyenv.run | bash; \
		fi; \
		$(MAKE) setup-pyenv-shell; \
	else \
		echo "✅ pyenv is already installed"; \
	fi

# Check and install pyenv-virtualenv
check-install-pyenv-virtualenv:
	@echo "🔍 Checking pyenv-virtualenv installation..."
	@if ! pyenv commands | grep -q virtualenv; then \
		echo "📦 Installing pyenv-virtualenv..."; \
		if [[ "$(shell uname)" == "Darwin" ]]; then \
			if command -v brew &> /dev/null; then \
				brew install pyenv-virtualenv; \
			else \
				echo "❌ Homebrew not found. Please install Homebrew first."; \
				exit 1; \
			fi; \
		else \
			git clone https://github.com/pyenv/pyenv-virtualenv.git $$(pyenv root)/plugins/pyenv-virtualenv; \
		fi; \
		$(MAKE) setup-pyenv-virtualenv-shell; \
	else \
		echo "✅ pyenv-virtualenv is already installed"; \
	fi

# Create virtual environment
create-virtualenv:
	@echo "🏗️  Creating virtual environment..."
	@if ! pyenv versions | grep -q "$(PYTHON_VERSION)"; then \
		echo "📦 Installing Python $(PYTHON_VERSION)..."; \
		pyenv install $(PYTHON_VERSION); \
	fi
	@if ! pyenv versions | grep -q "$(VENV_NAME)"; then \
		echo "🔧 Creating virtual environment $(VENV_NAME)..."; \
		pyenv virtualenv $(PYTHON_VERSION) $(VENV_NAME); \
		echo "✅ Virtual environment $(VENV_NAME) created"; \
	else \
		echo "✅ Virtual environment $(VENV_NAME) already exists"; \
	fi

# Set default virtual environment
set-default-virtualenv:
	@echo "🎯 Setting default virtual environment..."
	@pyenv local $(VENV_NAME)
	@echo "✅ Virtual environment $(VENV_NAME) set as default for this project"

# Check and install poetry
check-install-poetry:
	@echo "🔍 Checking poetry installation..."
	@if ! command -v poetry &> /dev/null; then \
		echo "📦 Installing poetry..."; \
		curl -sSL https://install.python-poetry.org | python3 -; \
		$(MAKE) setup-poetry-shell; \
	else \
		echo "✅ poetry is already installed"; \
	fi

# Install dependencies
install-dependencies:
	@echo "📦 Installing project dependencies..."
	@if command -v poetry &> /dev/null; then \
		poetry sync --no-root; \
		echo "✅ Dependencies installed successfully"; \
	else \
		echo "❌ Poetry not found in PATH. Please restart your shell and try again."; \
		exit 1; \
	fi

# Clean up virtual environment
clean:
	@echo "🧹 Cleaning up virtual environment..."
	@if pyenv versions | grep -q "$(VENV_NAME)"; then \
		pyenv uninstall -f $(VENV_NAME); \
		echo "✅ Virtual environment $(VENV_NAME) removed"; \
	else \
		echo "ℹ️  Virtual environment $(VENV_NAME) not found"; \
	fi
	@if [ -f .python-version ]; then \
		rm .python-version; \
		echo "✅ Local Python version file removed"; \
	fi

# Run code linting
lint:
	@echo "🔍 Running code linting..."
	@if command -v poetry &> /dev/null; then \
		echo "📝 Running black (code formatter)..."; \
		poetry run black --check --diff .; \
		echo "🔧 Running isort (import sorter)..."; \
		poetry run isort --check-only --diff .; \
		echo "🔎 Running pyright (type checker)..."; \
		poetry run pyright; \
		echo "✅ All linting checks completed"; \
	else \
		echo "❌ Poetry not found in PATH. Please run 'make init' first."; \
		exit 1; \
	fi

# Helper functions for shell setup
get-shell-rc:
	@if echo "$$SHELL" | grep -q "zsh"; then \
		echo "$$HOME/.zshrc"; \
	elif echo "$$SHELL" | grep -q "bash"; then \
		echo "$$HOME/.bashrc"; \
	else \
		echo "$$HOME/.zshrc"; \
	fi

# Setup pyenv in shell configuration
setup-pyenv-shell:
	@echo "🔧 Setting up pyenv in shell configuration..."
	@SHELL_RC=$$($(MAKE) get-shell-rc -s); \
	if [ ! -f "$$SHELL_RC" ]; then \
		touch "$$SHELL_RC"; \
	fi; \
	cp "$$SHELL_RC" "$$SHELL_RC.backup.$$(date +%Y%m%d_%H%M%S)" 2>/dev/null || true; \
	if ! grep -q "PYENV_ROOT" "$$SHELL_RC"; then \
		echo "" >> "$$SHELL_RC"; \
		echo "# pyenv configuration" >> "$$SHELL_RC"; \
		echo "export PYENV_ROOT=\"\$$HOME/.pyenv\"" >> "$$SHELL_RC"; \
		echo "[[ -d \$$PYENV_ROOT/bin ]] && export PATH=\"\$$PYENV_ROOT/bin:\$$PATH\"" >> "$$SHELL_RC"; \
		echo "eval \"\$$(pyenv init -)\"" >> "$$SHELL_RC"; \
		echo "✅ pyenv configuration added to $$SHELL_RC"; \
	else \
		echo "✅ pyenv already configured in $$SHELL_RC"; \
	fi

# Setup pyenv-virtualenv in shell configuration
setup-pyenv-virtualenv-shell:
	@echo "🔧 Setting up pyenv-virtualenv in shell configuration..."
	@SHELL_RC=$$($(MAKE) get-shell-rc -s); \
	if [ ! -f "$$SHELL_RC" ]; then \
		touch "$$SHELL_RC"; \
	fi; \
	cp "$$SHELL_RC" "$$SHELL_RC.backup.$$(date +%Y%m%d_%H%M%S)" 2>/dev/null || true; \
	if ! grep -q "pyenv virtualenv-init" "$$SHELL_RC"; then \
		echo "" >> "$$SHELL_RC"; \
		echo "# pyenv-virtualenv configuration" >> "$$SHELL_RC"; \
		echo "eval \"\$$(pyenv virtualenv-init -)\"" >> "$$SHELL_RC"; \
		echo "✅ pyenv-virtualenv configuration added to $$SHELL_RC"; \
	else \
		echo "✅ pyenv-virtualenv already configured in $$SHELL_RC"; \
	fi

# Setup poetry in shell configuration
setup-poetry-shell:
	@echo "🔧 Setting up poetry in shell configuration..."
	@SHELL_RC=$$($(MAKE) get-shell-rc -s); \
	if [ ! -f "$$SHELL_RC" ]; then \
		touch "$$SHELL_RC"; \
	fi; \
	cp "$$SHELL_RC" "$$SHELL_RC.backup.$$(date +%Y%m%d_%H%M%S)" 2>/dev/null || true; \
	if ! grep -q "/.local/bin" "$$SHELL_RC"; then \
		echo "" >> "$$SHELL_RC"; \
		echo "# poetry configuration" >> "$$SHELL_RC"; \
		echo "export PATH=\"\$$HOME/.local/bin:\$$PATH\"" >> "$$SHELL_RC"; \
		echo "✅ poetry PATH configuration added to $$SHELL_RC"; \
	else \
		echo "✅ poetry PATH already configured in $$SHELL_RC"; \
	fi

# Reload shell configuration
reload-shell-config:
	@echo "🔄 Reloading shell configuration..."
	@SHELL_RC=$$($(MAKE) get-shell-rc -s); \
	if [ -f "$$SHELL_RC" ]; then \
		echo "📁 Sourcing $$SHELL_RC"; \
		if echo "$$SHELL" | grep -q "zsh"; then \
			zsh -c "source $$SHELL_RC && echo '✅ Shell configuration reloaded successfully (zsh)!'" || \
			echo "⚠️  Note: Some zsh changes may require a full shell restart"; \
		elif echo "$$SHELL" | grep -q "bash"; then \
			bash -c "source $$SHELL_RC && echo '✅ Shell configuration reloaded successfully (bash)!'" || \
			echo "⚠️  Note: Some bash changes may require a full shell restart"; \
		else \
			$$SHELL -c "source $$SHELL_RC && echo '✅ Shell configuration reloaded successfully!'" || \
			echo "⚠️  Note: Some changes may require a full shell restart"; \
		fi; \
	else \
		echo "⚠️  Shell configuration file not found: $$SHELL_RC"; \
	fi

# Restart shell (provides instructions and helper)
restart-shell:
	@echo "🔄 Restarting shell..."
	@echo "💡 Choose one of these options:"
	@echo ""
	@echo "  1️⃣  Quick reload (recommended):"
	@SHELL_RC=$$($(MAKE) get-shell-rc -s); \
	if echo "$$SHELL" | grep -q "zsh"; then \
		echo "     source $$SHELL_RC  # (zsh)"; \
	elif echo "$$SHELL" | grep -q "bash"; then \
		echo "     source $$SHELL_RC  # (bash)"; \
	else \
		echo "     source $$SHELL_RC  # ($$(basename $$SHELL))"; \
	fi
	@echo ""
	@echo "  2️⃣  Full shell restart:"
	@echo "     exec $$SHELL"
	@echo ""
	@echo "  3️⃣  New terminal session:"
	@echo "     Open a new terminal window/tab"
	@echo ""
	@echo "🚀 Auto-executing option 1 (quick reload)..."
	@$(MAKE) reload-shell-config
