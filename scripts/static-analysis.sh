#!/bin/bash
set -e

# echo "Running mypy..."
mypy captn captn_agents google_ads openai_agent application.py

echo "Running bandit..."
bandit -c pyproject.toml -r captn captn_agents google_ads openai_agent application.py

echo "Running semgrep..."
semgrep scan --config auto --error
