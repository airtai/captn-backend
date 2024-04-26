#!/usr/bin/env bash

date=$(date +"%FT%T")
# delete after
date="test"

start=`date +%s`

# Generate the task table
python tests/benchmark/get_info_from_the_web_page.py generate-task-table --file-suffix $date

# Run the tests three in parallel
python tests/benchmark/get_info_from_the_web_page.py run-tests --file-suffix $date &
python tests/benchmark/get_info_from_the_web_page.py run-tests --file-suffix $date &
python tests/benchmark/get_info_from_the_web_page.py run-tests --file-suffix $date &
python tests/benchmark/get_info_from_the_web_page.py run-tests --file-suffix $date &
python tests/benchmark/get_info_from_the_web_page.py run-tests --file-suffix $date

end=`date +%s`
echo Total execution time: $((end-start))s
