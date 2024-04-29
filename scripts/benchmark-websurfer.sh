#!/usr/bin/env bash

date=$(date +"%FT%T")
# delete after
# date="test"

start=`date +%s`

# Generate the task table
python captn/captn_agents/backend/benchmarking/base.py generate-task-table-for-websurfer --output-dir benchmarking/working --file-name "websurfer-benchmark-task-list-$date"

# Run the tests three in parallel
# python tests/benchmark/get_info_from_the_web_page.py run-tests --file-suffix $date &
# python tests/benchmark/get_info_from_the_web_page.py run-tests --file-suffix $date &
python captn/captn_agents/backend/benchmarking/base.py run-tests --file-path "benchmarking/working/websurfer-benchmark-task-list-$date"

# end=`date +%s`
# echo Total execution time: $((end-start))s
