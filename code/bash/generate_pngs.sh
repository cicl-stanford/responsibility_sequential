#!/bin/bash

# specify the path of the directory to search for JSON files
world=world43
log_directory="./resources/episodes/${world}"
png_directory="./resources/stimuli/"
icon_directory="./resources/images/"

# find all files in log_directory that start with "manual_" and end with ".json"
log_files=$(find $log_directory -name "manuallogs*.json")
for log_file in $log_files; do
    echo "Processing $log_file"
    # for each file, run the png generation code
    python python/generate_pngs.py --log_file=$log_file --png_directory=$png_directory --icon_directory=$icon_directory --loop_gif
done