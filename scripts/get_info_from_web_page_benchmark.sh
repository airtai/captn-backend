#!/usr/bin/env bash

date=$(date +"%FT%T")

python tests/benchmark/get_info_from_the_web_page.py --file-suffix $date & python tests/benchmark/get_info_from_the_web_page.py --file-suffix $date
python tests/benchmark/get_info_from_the_web_page.py --file-suffix $date & python tests/benchmark/get_info_from_the_web_page.py --file-suffix $date
