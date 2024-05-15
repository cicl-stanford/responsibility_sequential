#!/bin/bash

# Replace PLACEHOLDER with your working directory 
source {PLACEHOLDER}/env/bin/activate

# input parameters
world_name=$1       # the name of the world (e.g. "world43")
trial_name=$2       # the name of the trial (e.g. "trial1")
human_scaler=$3     # controls the stochasticity in the movements of the human agent
ai_scaler=$3        # controls the stochasticity in the movements of the ai agent
sim_scaler=$3       # controls the stochaticity in the internal simulation of the human agent

# fixed parameters
horizon=20
radius=1
ai_switching=0.0    # set switching to 0.0 because it is
human_switching=0.0 # a counterfactual simulation
traffic_delay=10
semi_manual_seed=42 # set the seed for the factual part of the simulation
agent_seeds=300     # set the number of counterfactual simulations

log_directory={PLACEHOLDER}/resources/episodes/
world_directory={PLACEHOLDER}/resources/worlds/

world_file=$world_directory$world_name.txt
################################
# JOB STARTS HERE
################################
echo $world_name $trial_name $sim_scaler

# set the responses file
responses_file=${log_directory}${world_name}/factual_responses:${world_name}_explanation:${trial_name}.pkl
cfy_responses_file=${log_directory}${world_name}/counterfactual_responses:${world_name}_explanation:${trial_name}_answer:yes.pkl
cfn_responses_file=${log_directory}${world_name}/counterfactual_responses:${world_name}_explanation:${trial_name}_answer:no.pkl

python python/utils.py --factual_responses_file=${responses_file} --yn=y --cf_responses_file=${cfy_responses_file}
python python/utils.py --factual_responses_file=${responses_file} --yn=n --cf_responses_file=${cfn_responses_file}

# run the simulations
for agent_seed in $(seq 1 $agent_seeds); do
    echo -ne "Agent seed: $agent_seed/$agent_seeds\r"
    python python/maze_problem.py --log_file=${log_directory}${world_name}/cfyeslogs:${world_name}_humanscaler:${human_scaler}_aiscaler:${ai_scaler}_simscaler:${sim_scaler}_agentseed:${agent_seed}_semimanualseed:${semi_manual_seed}.json --human_prob_estimates_file=${log_directory}${world_name}/humanprobs:${world_name}_simscaler:${sim_scaler}_semimanualseed:${semi_manual_seed}.json --world_file=$world_file --traffic_delay=$traffic_delay --sim_scaler=$sim_scaler --ai_switching=$ai_switching --human_switching=$human_switching --human_scaler=$human_scaler --ai_scaler=$ai_scaler --radius=$radius --agent_seed=$agent_seed --semi_manual_seed=$semi_manual_seed --override --responses_file=${cfy_responses_file} --horizon=$horizon
    python python/maze_problem.py --log_file=${log_directory}${world_name}/cfnologs:${world_name}_humanscaler:${human_scaler}_aiscaler:${ai_scaler}_simscaler:${sim_scaler}_agentseed:${agent_seed}_semimanualseed:${semi_manual_seed}.json --human_prob_estimates_file=${log_directory}${world_name}/humanprobs:${world_name}_simscaler:${sim_scaler}_semimanualseed:${semi_manual_seed}.json --world_file=$world_file --traffic_delay=$traffic_delay --sim_scaler=$sim_scaler --ai_switching=$ai_switching --human_switching=$human_switching --human_scaler=$human_scaler --ai_scaler=$ai_scaler --radius=$radius --agent_seed=$agent_seed --semi_manual_seed=$semi_manual_seed --override --responses_file=${cfn_responses_file} --horizon=$horizon
done

# iterate over the generated json files of the simulations, and get the respective duration needed to reach the goal
lengths=()
successes=()
for file in ${log_directory}${world_name}/cfyeslogs:${world_name}_humanscaler:${human_scaler}_aiscaler:${ai_scaler}*.json; do
    # find the episode length (in time) and append it to the array
    length=$(jq '.length' ${file})
    length=$((length - 1))
    lengths+=($length)
    # if length <= t_remaining set success to 1, else set it to 0
    if [ $length -le $horizon ]; then
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
echo $json > ${log_directory}${world_name}/cfyesreport:${world_name}_humanscaler:${human_scaler}_aiscaler:${ai_scaler}.json;



# iterate over the generated json files of the simulations, and get the respective duration needed to reach the goal
lengths=()
successes=()
for file in ${log_directory}${world_name}/cfnologs:${world_name}_humanscaler:${human_scaler}_aiscaler:${ai_scaler}*.json; do
    # find the episode length (in time) and append it to the array
    length=$(jq '.length' ${file})
    length=$((length - 1))
    lengths+=($length)
    # if length <= t_remaining set success to 1, else set it to 0
    if [ $length -le $horizon ]; then
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
echo $json > ${log_directory}${world_name}/cfnoreport:${world_name}_humanscaler:${human_scaler}_aiscaler:${ai_scaler}.json;