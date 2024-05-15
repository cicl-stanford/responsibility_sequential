#!/bin/bash

# Replace PLACEHOLDER with the full path of your working directory 
single_experiment_file={PLACEHOLDER}/code/bash/generate_counterfactual_episodes_slurm.sh

# slurm parameters
job_mem=1G
job_time=0-00:20
job_partition=spyder

# grid parameters: the world, episode trial, and time remaining cutoff
world_order=(world43 world44 world45 world46 world47 world48 world57 world58 world49 world50 world55 world56 world51 world52 world53 world54)
trial_order=(trial1 trial2 trial3 trial4 trial5 trial6 trial7 trial8 trial9 trial10 trial11 trial12 trial13 trial14 trial15 trial16)
human_scalers=(0.6 0.8 1.0 1.2 1.4 1.6 1.8 2.0)

# iterate over the indices of world_order
for world_idx in ${!world_order[@]}; do
    # get the world name
    world_name=${world_order[$world_idx]}
    # get the trial name
    trial_name=${trial_order[$world_idx]}
    # iterate over the human scalers
    for human_scaler in ${human_scalers[@]}; do
        # submit the job
        sbatch -c 1 -o slurmcf:${world_name}_humanscaler:${human_scaler}.out -e slurmcf:${world_name}_humanscaler:${human_scaler}.err --mem=$job_mem --time=$job_time --partition=$job_partition $single_experiment_file $world_name $trial_name $human_scaler
    done
done