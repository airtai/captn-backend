#!/usr/bin/env bash

start=`date +%s`

date=$(date +"%FT%T")
output_dir="benchmarking/working"
file_name="brief-creation-benchmark-task-list-$date.csv"

echo "Output directory: $output_dir"
echo "File name: $file_name"
# Generate the task table
benchmark generate-task-table-for-brief-creation --output-dir $output_dir --file-name $file_name

echo "File path: $output_dir/$file_name"
# Run the tests three in parallel
# benchmark run-tests --file-path "$output_dir/$file_name"

end=`date +%s`
echo Total execution time: $((end-start))s
