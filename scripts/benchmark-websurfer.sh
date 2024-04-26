#!/usr/bin/env bash

date=$(date +"%FT%T")

start=`date +%s`

# Run the tests three in parallel
python tests/benchmark/get_info_from_the_web_page.py run-tests --file-suffix $date &
python tests/benchmark/get_info_from_the_web_page.py run-tests --file-suffix $date


# python tests/benchmark/get_info_from_the_web_page.py run-tests --file-suffix $date &
# python tests/benchmark/get_info_from_the_web_page.py run-tests --file-suffix $date

end=`date +%s`
echo Total execution time: $((end-start))s

# Generate the aggregated report
python tests/benchmark/get_info_from_the_web_page.py generate-aggregated-report --file-suffix $date
