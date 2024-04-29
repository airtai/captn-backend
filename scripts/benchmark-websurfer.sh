#!/usr/bin/env bash

date=$(date +"%FT%T")
# delete after
# date="test"

start=`date +%s`

# Generate the task table
benchmark generate-task-table-for-websurfer --output-dir benchmarking/working --file-name "websurfer-benchmark-task-list-$date"

# Run the tests three in parallel
benchmark run-tests --file-path "benchmarking/working/websurfer-benchmark-task-list-$date"

end=`date +%s`
echo Total execution time: $((end-start))s
