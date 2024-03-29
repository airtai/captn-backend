#!/bin/bash

echo "Running pyup_dirs..."
pyup_dirs --py38-plus --recursive captn google_ads openai_agent tests application.py

# echo "Running isort..."
# isort captn captn_agents google_ads openai_agent application.py

echo "Running ruff check..."
ruff check --fix

echo "Running ruff formatter (black replacement)..."
ruff format

# echo "Running black..."
# black captn google_ads openai_agent tests application.py
