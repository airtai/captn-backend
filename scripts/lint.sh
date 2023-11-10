#!/bin/bash

echo "Running pyup_dirs..."
pyup_dirs --py38-plus --recursive captn google_ads openai_agent application.py

echo "Running isort..."
isort captn google_ads openai_agent application.py

echo "Running black..."
black captn google_ads openai_agent application.py