SHELL := /bin/zsh

GREEN := \033[1;32m
RED   := \033[1;31m
BLUE  := \033[1;36m
RESET := \033[0m

VENV = venv
VENV_BIN = $(VENV)/bin
PYTHON = $(VENV_BIN)/python
PIP = $(VENV_BIN)/pip

MY_Flags = --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

install: $(VENV)

$(VENV):
	@echo "$(GREEN)Creating virtual environment via python3 -m venv...$(RESET)"
	@python3 -m venv $(VENV)
	
	@echo "\n$(BLUE)Upgrading pip...$(RESET)"
	@$(PIP) install --upgrade pip
	
	@echo "\n$(BLUE)Installing dependencies...$(RESET)"
	@$(PIP) install pyglet flake8 mypy


run: $(VENV)
	@chmod +x assets/select_map.sh
	@zsh ./assets/select_map.sh || true


debug: $(VENV)
	@echo "$(GREEN)Launching simulation with pdb debugger...$(RESET)"
	@$(PYTHON) -m pdb fly-in.py


clean:
	@echo "$(RED)Cleaning up caches...$(RESET)"
	@rm -rf __pycache__ src/__pycache__ .mypy_cache .pytest_cache
	@echo "$(RED)Cleaning up virtual environment...$(RESET)"
	@rm -rf $(VENV)


lint: $(VENV)
	@echo "$(GREEN)Running flake8 syntax checks...$(RESET)"
	@-$(VENV_BIN)/flake8 *.py
	@echo "$(GREEN)Running mypy strict type analysis...$(RESET)"
	@-$(VENV_BIN)/mypy *.py $(MY_Flags)

.PHONY: install run debug clean lint lint-strict
