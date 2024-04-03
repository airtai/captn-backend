#!/bin/bash
set -e

# echo "Running mypy..."
mypy captn

echo "Running bandit..."
bandit -c pyproject.toml -r captn google_ads openai_agent application.py

echo "Running semgrep..."
semgrep scan --config auto --error
