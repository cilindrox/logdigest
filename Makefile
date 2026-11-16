MAKEFLAGS += --warn-undefined-variables --no-builtin-rules
SHELL := /usr/bin/env bash

# The `--norc` option prevents "PS1: unbound" errors.
# If Bash thinks it is being run with its standard input connected to a network
# connection (such as via SSH or via Docker), it reads and executes commands
# from ~/.bashrc, regardless of whether it thinks it is in interactive mode.
# Bash does not set PS1 in non-interactive environments. But on Ubuntu 24.04 the
# default /etc/bash.bashrc file assumes that PS1 is set.
#
# See https://www.gnu.org/software/bash/manual/bash.html#Invoked-by-remote-shell-daemon
.SHELLFLAGS := --norc -euo pipefail -c
.DEFAULT_GOAL := help
.DELETE_ON_ERROR:
.SUFFIXES:

# Set empty value for MAKECMDGOALS to prevent the "warning: undefined variable 'MAKECMDGOALS'"
# warning from happening when running make without arguments
MAKECMDGOALS ?=

##@ Linting and static checks

.PHONY: lint mypy ruff

lint: ruff mypy  ## Lint files

mypy:  ## Run mypy
	@mypy

ruff:  ## Run ruff check
	@ruff check .

##@ Testing

.PHONY: test test-cov-html

test: lint  ## Run tests
	@pytest

test-cov: lint  ## Run test coverage
	@pytest -q --cov=logdigest --cov-report=term-missing

test-cov-html: lint  ## Run test coverage
	@pytest -q --cov=logdigest --cov-report=term-missing --cov-report=html && \
		open htmlcov/index.html

##@ Helpers
.PHONY: help

# See: https://www.thapaliya.com/en/writings/well-documented-makefiles/
help:  ## Display this help
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)
