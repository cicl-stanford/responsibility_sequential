#!/bin/bash

# constants
log_directory=./resources/episodes/
world_directory=./resources/worlds/
sim_scaler=3.0
radius=1
agent_seed=42

# params
traffic_delay=10
world_name=world43
world_file=$world_directory$world_name.txt
horizon=20

# make directory if non existing
mkdir -p $log_directory$world_name

# set the responses file
responses_file=${log_directory}${world_name}/factual_responses:${world_name}.pkl

python python/maze_problem.py --log_file=${log_directory}${world_name}/manuallogs:${world_name}_delay:${traffic_delay}_simscaler:${sim_scaler}_radius:${radius}.json --world_file=$world_file --traffic_delay=$traffic_delay --sim_scaler=$sim_scaler --radius=$radius --verbose=1 --override --responses_file=${responses_file} --agent_seed=$agent_seed --horizon=$horizon