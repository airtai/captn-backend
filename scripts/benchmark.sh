#!/usr/bin/env bash

team_name="brief-creation"
avaliable_teams=("brief-creation" "campaign-creation" "websurfer" "end2end" "weekly-analysis")

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

# if team name is 'all' , create teams_list equal to avaliable_teams
if [ "$team_name" == "all" ]; then
    teams_list=("${avaliable_teams[@]}")
    echo "Benchmarking all teams: ${teams_list[@]}"
# check if the team name is valid
elif [[ ! " ${avaliable_teams[@]} " =~ " ${team_name} " ]]; then
    echo "Invalid team name: $team_name"
    echo "Available team names: ${avaliable_teams[@]}"
    exit 1
else
    teams_list=("$team_name")
    echo "Benchmarking team: $team_name"
fi

date=$(date +"%FT%T")
for team_name in "${teams_list[@]}"; do
    echo "Team name: $team_name"

    start=`date +%s`

    output_dir="benchmarking/working/$date"
    file_name="$team_name-benchmark-task-list.csv"

    echo "Output directory: $output_dir"
    echo "File name: $file_name"

    # Generate the task table
    if [ "$team_name" == "brief-creation" ]; then
        benchmark generate-task-table-for-brief-creation --output-dir $output_dir --file-name $file_name
    elif [ "$team_name" == "campaign-creation" ]; then
        benchmark generate-task-table-for-campaign-creation --output-dir $output_dir --file-name $file_name
    elif [ "$team_name" == "end2end" ]; then
        benchmark generate-task-table-for-campaign-creation --output-dir $output_dir --file-name $file_name --end2end
    elif [ "$team_name" == "websurfer" ]; then
        benchmark generate-task-table-for-websurfer --output-dir $output_dir --file-name $file_name
    elif [ "$team_name" == "weekly-analysis" ]; then
        benchmark generate-task-table-for-weekly-analysis --output-dir $output_dir --file-name $file_name
    fi

    echo "File path: $output_dir/$file_name"
    mkdir -p "$output_dir/logs"
    benchmark run-tests --file-path "$output_dir/$file_name" > "$output_dir/logs/$team_name-benchmark-result.txt"

    end=`date +%s`
    echo Total execution time: $((end-start))s
done
