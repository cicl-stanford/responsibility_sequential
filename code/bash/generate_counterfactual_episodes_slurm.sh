#!/bin/bash

# Replace PLACEHOLDER with your working directory 
source {PLACEHOLDER}/env/bin/activate

# input parameters
world_name=$1       # the name of the world (e.g. "world43")
trial_name=$2       # the name of the trial (e.g. "trial1")
human_scaler=$3     # controls the stochasticity in the movements of the human agent
ai_scaler=$3        # controls the stochasticity in the movements of the ai agent

# fixed parameters
seed=42
t_remaining=20
radius=1
ai_switching=0.0    # set switching to 0.0 because it is
human_switching=0.0 # a counterfactual simulation
traffic_delay=10
agent_seeds=300     # set the number of counterfactual simulations
initial_agent=human

log_directory={PLACEHOLDER}/resources/episodes/
world_directory={PLACEHOLDER}/resources/worlds/

world_file=$world_directory$world_name.txt

################################
# JOB STARTS HERE
################################
echo $world_name $trial_name $human_scaler

# run the simulations
for agent_seed in $(seq 1 $agent_seeds); do
    echo -ne "Agent seed: $agent_seed/$agent_seeds\r"
    python python/maze_problem.py --log_file=${log_directory}${world_name}/cflogs:${world_name}_humanscaler:${human_scaler}_aiscaler:${ai_scaler}_agentseed:${agent_seed}.json --world_file=$world_file --traffic_delay=$traffic_delay --ai_switching=$ai_switching --human_switching=$human_switching --human_scaler=$human_scaler --ai_scaler=$ai_scaler --radius=$radius --agent_seed=$agent_seed --initial_agent=$initial_agent
done

# iterate over the generated json files of the simulations, and get the respective duration needed to reach the goal
lengths=()
successes=()
for file in ${log_directory}${world_name}/cflogs:${world_name}_humanscaler:${human_scaler}_aiscaler:${ai_scaler}*.json; do
    # find the episode length (in time) and append it to the array
    length=$(jq '.length' ${file})
    length=$((length - 1))
    lengths+=($length)
    # if length <= t_remaining set success to 1, else set it to 0
    if [ $length -le $t_remaining ]; then
        success=1
    else
        success=0
    fi
    successes+=($success)
    # delete the intermediate log files
    rm ${file}
done

# compute the mean
sum=0
num_elements=${#lengths[@]}
for i in "${lengths[@]}"; do
    sum=$((sum + i))
done
mean=$(echo "scale=2; $sum / $num_elements" | bc)

# compute the standard deviation
sum=0
for i in "${lengths[@]}"; do
    sum=$(echo "scale=2; $sum + ($i - $mean)^2" | bc)
done
std=$(printf "%.2f" $(echo "scale=2; sqrt($sum / $num_elements)" | bc))

# write the mean duration, the standard deviation and the full arrays of durations and successes to a new JSON file (counterfactual report)
json_array_lengths=$(printf '%d\n' "${lengths[@]}" | jq -s .)
json_array_successes=$(printf '%d\n' "${successes[@]}" | jq -s .)
json="{ \"mean_duration\": $mean, \"std\": $std, \"lengths\": $json_array_lengths, \"successes\": $json_array_successes }"
echo $json > ${log_directory}${world_name}/cfreport:${world_name}_humanscaler:${human_scaler}_aiscaler:${ai_scaler}.json;

deactivate