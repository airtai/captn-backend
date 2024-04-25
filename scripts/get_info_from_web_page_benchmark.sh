#!/usr/bin/env bash

date=$(date +"%FT%T")


# Run the tests two in parallel
python tests/benchmark/get_info_from_the_web_page.py run-tests --file-suffix $date & python tests/benchmark/get_info_from_the_web_page.py run-tests --file-suffix $date
python tests/benchmark/get_info_from_the_web_page.py run-tests --file-suffix $date & python tests/benchmark/get_info_from_the_web_page.py run-tests --file-suffix $date


# Generate the aggregated report
python tests/benchmark/get_info_from_the_web_page.py generate-aggregated-report --file-suffix $date
