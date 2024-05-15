# Bash readme

* `generate_episodes.sh` simulates counterfactual episodes where the human drives on their own. It uses multiple seeds, since the human's behavior in the counterfactual simulation is stochastic.
* `generate_manual_episodes.sh` simulates factual episodes, where prompts and agent choices are given manually as (keyboard) input at each time step.
* `generate_pngs.sh` takes as input the logged episodes from the previous scripts and creates pngs and gifs.
* `generate_world.sh` randomly generates worlds based on the user's (keyboard) input.