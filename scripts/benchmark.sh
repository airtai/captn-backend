#!/usr/bin/env bash

team_name="brief-creation"
avaliable_teams=("brief-creation" "campaign-creation" "websurfer")

while getopts ":t:" opt; do
    case ${opt} in
        t )
            team_name=$OPTARG
            ;;
        \? )
            echo "Usage: cmd [-t team_name]"
            ;;
    esac
done

# check if the team name is valid
if [[ ! " ${avaliable_teams[@]} " =~ " ${team_name} " ]]; then
    echo "Invalid team name: $team_name"
    echo "Available team names: ${avaliable_teams[@]}"
    exit 1
fi

echo "Team name: $team_name"

start=`date +%s`

date=$(date +"%FT%T")
output_dir="benchmarking/working"
file_name="$team_name-benchmark-task-list-$date.csv"

echo "Output directory: $output_dir"
echo "File name: $file_name"

# Generate the task table
if [ "$team_name" == "brief-creation" ]; then
    benchmark generate-task-table-for-brief-creation --output-dir $output_dir --file-name $file_name
elif [ "$team_name" == "campaign-creation" ]; then
    benchmark generate-task-table-for-campaign-creation --output-dir $output_dir --file-name $file_name
elif [ "$team_name" == "websurfer" ]; then
    benchmark generate-task-table-for-websurfer --output-dir $output_dir --file-name $file_name
fi

echo "File path: $output_dir/$file_name"
mkdir -p "$output_dir/logs"
benchmark run-tests --file-path "$output_dir/$file_name" > "$output_dir/logs/$team_name-benchmark-result-$date.txt"

end=`date +%s`
echo Total execution time: $((end-start))s
