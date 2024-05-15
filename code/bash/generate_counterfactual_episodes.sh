#!/bin/bash

# constants
log_directory=./resources/episodes/
world_directory=./resources/worlds/
radius=1
# the following are important for the counterfactual simulations
sim_scaler=1.0      # controls the stochaticity in the internal simulation of the human agent
ai_switching=0.0    # set switching to 0.0 because it is
human_switching=0.0 # a counterfactual simulation
traffic_delay=10

############ PARAMS ############
human_scaler=3.0    # controls the stochasticity in the movements of the human agent
ai_scaler=3.0       # controls the stochasticity in the movements of the ai agent
agent_seeds=30     # set the number of counterfactual simulations    

# uncomment the respective line to choose the agent
initial_agent=human
# initial_agent=ai

world_name=world43
explanation=trial1
time_remaining=20

world_file=$world_directory$world_name.txt

################################

# make a directory if not existing
mkdir -p $log_directory$world_name

# run the simulations
for agent_seed in $(seq 1 $agent_seeds); do
    echo -ne "Agent seed: $agent_seed/$agent_seeds\r"
    python python/maze_problem.py --log_file=${log_directory}${world_name}/cflogs:${world_name}_simscaler:${sim_scaler}_humanscaler:${human_scaler}_aiscaler:${ai_scaler}_agentseed:${agent_seed}.json --world_file=$world_file --traffic_delay=$traffic_delay --sim_scaler=$sim_scaler --ai_switching=$ai_switching --human_switching=$human_switching --human_scaler=$human_scaler --ai_scaler=$ai_scaler --radius=$radius --agent_seed=$agent_seed --initial_agent=$initial_agent
done

# iterate over the generated json files of the simulations, and get the respective duration needed to reach the goal
lengths=()
successes=()
for file in ${log_directory}${world_name}/cflogs:${world_name}_simscaler:${sim_scaler}_humanscaler:${human_scaler}_aiscaler:${ai_scaler}*.json; do
    # find the episode length (in time) and append it to the array
    length=$(jq '.length' ${file})
    length=$((length - 1))
    lengths+=($length)
    # if length <= t_remaining set success to 1, else set it to 0
    if [ $length -le $time_remaining ]; then
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
std=$(echo "scale=2; sqrt($sum / $num_elements)" | bc)

# write the mean duration, the standard deviation and the full arrays of durations and successes to a new JSON file (counterfactual report)
json_array_lengths=$(printf '%d\n' "${lengths[@]}" | jq -s .)
json_array_successes=$(printf '%d\n' "${successes[@]}" | jq -s .)
json="{ \"mean_duration\": $mean, \"std\": $std, \"lengths\": $json_array_lengths, \"successes\": $json_array_successes }"
echo $json > ${log_directory}${world_name}/cfreport:${world_name}_simscaler:${sim_scaler}_humanscaler:${human_scaler}_aiscaler:${ai_scaler}.json;