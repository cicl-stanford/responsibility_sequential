#!/bin/bash

# constants
log_directory=./resources/episodes/
world_order=(world43 world44 world45 world46 world47 world48 world57 world58 world49 world50 world55 world56 world51 world52 world53 world54)
trial_order=(trial1 trial2 trial3 trial4 trial5 trial6 trial7 trial8 trial9 trial10 trial11 trial12 trial13 trial14 trial15 trial16)
t_remaining=20

################################

# iterate over the indices of world_order
for world_idx in ${!world_order[@]}; do
    # get the world name
    world_name=${world_order[$world_idx]}
    # get the trial name
    trial_name=${trial_order[$world_idx]}
    # set the manual logs filename (starts with manuallogs:$world_name)
    logs_file=${log_directory}${world_name}/manuallogs:${world_name}_*_explanation:${trial_name}.json

    # open the manuallogs json file, in the array time_steps count the number of steps before time=t_remaining where agent_name=human
    # and agent_name=ai, and store the results in 2 variables
    human_count=$(jq --arg t_remaining "$t_remaining" --arg agent_name "human" '.time_steps | map(select(.time <= ($t_remaining | tonumber) and .agent_name == $agent_name)) | length' $logs_file)
    ai_count=$(jq --arg t_remaining "$t_remaining" --arg agent_name "ai" '.time_steps | map(select(.time <= ($t_remaining | tonumber) and .agent_name == $agent_name)) | length' $logs_file)

    json="{ \"human_count\": $human_count, \"ai_count\": $ai_count }"
    echo $json > ${log_directory}${world_name}/heurreport:${world_name}.json;
done