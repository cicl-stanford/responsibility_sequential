import pomdp_py
from agent import CompactBelief, LazyAgent
from utils import parse_initial_state
from domain import MazeState
from models import PolicyModel, TransitionModel, ObservationModel, RewardModel
from itertools import chain, combinations, product
import copy
from numpy.random import default_rng
import click
from planner import Planner
import json
import numpy as np
import pickle as pkl

def powerset(iterable):
    s = list(iterable)
    return chain.from_iterable(combinations(s, r) for r in range(len(s)+1))

class NpEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super(NpEncoder, self).default(obj)

class MazeProblem(pomdp_py.POMDP):
    """
    In fact, creating a MazeProblem class is entirely optional
    to simulate and solve POMDPs. But this is just an example
    of how such a class can be created.
    """

    def __init__(self, traffic_delay, radius, init_true_state, ai_init_belief, human_init_belief, human_scaler, ai_scaler, agent_seed, ai_switching, human_switching, sim_scaler):

        self.traffic_delay = traffic_delay
        self.radius = radius
        self.human_scaler = human_scaler
        self.ai_scaler = ai_scaler
        self.sim_scaler = sim_scaler
        self.agent_seed = agent_seed
        self.ai_switching = ai_switching
        self.human_switching = human_switching

        self.ai_agent = LazyAgent(ai_init_belief,
                               PolicyModel(ai_scaler, ai_switching),
                               TransitionModel(traffic_delay),
                               ObservationModel(radius, 'ai'),
                               RewardModel(),
                               'ai')
        self.human_agent = LazyAgent(human_init_belief,
                               PolicyModel(human_scaler, human_switching),
                               TransitionModel(traffic_delay),
                               ObservationModel(radius, 'human'),
                               RewardModel(),
                               'human')
        self.env = pomdp_py.Environment(init_true_state,
                                   TransitionModel(traffic_delay),
                                   RewardModel())


    @staticmethod
    def create(init_true_state, agent_seed, traffic_delay=10, radius=1, human_scaler=None, ai_scaler=None, ai_switching=0.2, human_switching=0.0, human_simulation_belief=None, ai_simulation_belief=None, sim_scaler=1.0):
        
        # initialize beliefs (compact representation) for ai & human
        accident_loc = [-1, -1]
        ai_closure_loc = [-1, -1]
        human_closure_loc = init_true_state.closure_loc
        ai_traffic_locs = copy.deepcopy(init_true_state.traffic_locs)
        human_traffic_locs = [[traffic_loc[0], traffic_loc[1], 0.5] for traffic_loc in init_true_state.traffic_locs]

        if ai_simulation_belief is not None:
            ai_init_belief = copy.deepcopy(ai_simulation_belief)
        else:
            ai_init_belief = CompactBelief(init_true_state.maze_map, init_true_state.vehicle_loc, init_true_state.goal_loc, ai_traffic_locs, accident_loc, ai_closure_loc)

        if human_simulation_belief is not None:
            human_init_belief = copy.deepcopy(human_simulation_belief)
        else:
            human_init_belief = CompactBelief(init_true_state.maze_map, init_true_state.vehicle_loc, init_true_state.goal_loc, human_traffic_locs, accident_loc, human_closure_loc)

        maze_problem = MazeProblem(traffic_delay, radius, init_true_state, ai_init_belief, human_init_belief, human_scaler, ai_scaler, agent_seed, ai_switching, human_switching, sim_scaler)
        maze_problem.ai_agent.set_belief(ai_init_belief, prior=True)
        maze_problem.human_agent.set_belief(human_init_belief, prior=True)
        
        # get initial observation from the environment
        ai_observation = maze_problem.ai_agent.observation_model.sample(init_true_state)
        human_observation = maze_problem.human_agent.observation_model.sample(init_true_state)
        
        # add observations to the agents' histories
        maze_problem.ai_agent.update_history(None, ai_observation)
        maze_problem.human_agent.update_history(None, human_observation)

        # update the agents' beliefs
        new_ai_belief, new_human_belief = update_beliefs(maze_problem, ai_observation, human_observation)
        maze_problem.ai_agent.set_belief(new_ai_belief)
        maze_problem.human_agent.set_belief(new_human_belief)        

        return maze_problem

def plan(maze_problem):
    
    costs_to_go = {'ai': {}, 'human': {}}
    
    # ai planning
    planner = Planner(maze_problem.ai_agent.belief.maze_map, maze_problem.ai_agent.belief.goal_loc, maze_problem.ai_agent.belief.accident_loc, maze_problem.ai_agent.belief.closure_loc, \
                maze_problem.ai_agent.belief.traffic_locs, maze_problem.env.transition_model.traffic_delay, agent_name='ai') 
    costs_to_go['ai'][str(maze_problem.ai_agent.belief.traffic_locs)] = planner.dijkstra()
    
    # plan according to human belief
    # generate all combinations of human_agent.belief.traffic_locs where the third element of each element is set to 0 or 1
    unknown_traffic_locs = [(ind, loc) for ind, loc in enumerate(maze_problem.human_agent.belief.traffic_locs) if loc[2] not in {0.0, 1.0}]
    unknown_traffic_loc_states = list(product([0.0, 1.0], repeat=len(unknown_traffic_locs)))
    
    # ai planning, simulated by the human
    traffic_locs = copy.deepcopy(maze_problem.human_agent.belief.traffic_locs)
    closure_loc = maze_problem.ai_agent.belief.closure_loc # NOTE: the human assumes that the ai doesn't have additional information about the closure location, other than what it has directly observed
    for unknown_traffic_loc_state in unknown_traffic_loc_states:
        for ind, loc in enumerate(unknown_traffic_locs):
            traffic_locs[loc[0]][2] = unknown_traffic_loc_state[ind]
        
        planner = Planner(maze_problem.human_agent.belief.maze_map, maze_problem.human_agent.belief.goal_loc, maze_problem.human_agent.belief.accident_loc, closure_loc, traffic_locs, \
                    maze_problem.env.transition_model.traffic_delay, agent_name='ai')
        costs_to_go['human'][str(traffic_locs)] = planner.dijkstra()

    # human planning
    traffic_locs = copy.deepcopy(maze_problem.human_agent.belief.traffic_locs)
    planner = Planner(maze_problem.human_agent.belief.maze_map, maze_problem.human_agent.belief.goal_loc, maze_problem.human_agent.belief.accident_loc, maze_problem.human_agent.belief.closure_loc, \
                    traffic_locs, maze_problem.env.transition_model.traffic_delay, agent_name='human')
    costs_to_go['human'][str(maze_problem.human_agent.belief.traffic_locs)] = planner.dijkstra()

    return costs_to_go

def time_step_printing(verbose, t, maze_problem, action, next_state, reward, ai_observation, human_observation):
    
    if verbose>0:
        print("Current state:\n", maze_problem.env.state)
        print("Action:", action)
        print("Reward:", reward)

    if verbose>1:
        print("Next state:", next_state)
        if maze_problem.env.state.agent_name == 'ai':
            print("AI Observation:", ai_observation)
        elif maze_problem.env.state.agent_name == 'human':
            print("Human Observation:", human_observation)

    

def update_explored_tiles(maze_problem, tiles_explored, state):
    # initialize all tiles as unexplored, except for the ones in the field of vision of the vehicle
    
    for loc in maze_problem.ai_agent.observation_model.get_field_of_vision(state):
        is_in_map_boundaries = (0 <= loc[0] < maze_problem.env.state.maze_map.shape[0]) and (0 <= loc[1] < maze_problem.env.state.maze_map.shape[1])
        if is_in_map_boundaries:
            tiles_explored[loc[0]][loc[1]] = 1

def update_logs(logs, maze_problem, action, codriver_action, tiles_explored, t):
    
    logs['time_steps'].append({
            'time' : t,
            'vehicle_loc' : copy.deepcopy(maze_problem.env.state.vehicle_loc),
            'time_idle' : copy.deepcopy(maze_problem.env.state.time_idle),
            'agent_name' : copy.deepcopy(maze_problem.env.state.agent_name),
            'action' : copy.deepcopy(action.dir),
            'codriver_action' : copy.deepcopy(codriver_action.dir),
            'tiles_explored' : copy.deepcopy(tiles_explored),
            'committed_action' : copy.deepcopy(maze_problem.env.state.committed_action),
        })

def update_beliefs(maze_problem, ai_observation, human_observation):
    
    # update the AI agent's belief
    new_ai_belief = CompactBelief(maze_problem.env.state.maze_map, maze_problem.env.state.vehicle_loc, maze_problem.env.state.goal_loc,\
                                copy.deepcopy(maze_problem.ai_agent.belief.traffic_locs), maze_problem.ai_agent.belief.accident_loc,\
                                maze_problem.ai_agent.belief.closure_loc, maze_problem.env.state.time_idle)
    if ai_observation.accident_loc != [-1, -1]:
        new_ai_belief.accident_loc = ai_observation.accident_loc
    if ai_observation.closure_loc != [-1, -1]:
        new_ai_belief.closure_loc = ai_observation.closure_loc

    # update the human agent's belief
    new_human_belief = CompactBelief(maze_problem.env.state.maze_map, maze_problem.env.state.vehicle_loc, maze_problem.env.state.goal_loc,\
                                copy.deepcopy(maze_problem.human_agent.belief.traffic_locs), maze_problem.human_agent.belief.accident_loc,\
                                maze_problem.human_agent.belief.closure_loc, maze_problem.env.state.time_idle)
    
    if human_observation.accident_loc != [-1, -1]:
        new_human_belief.accident_loc = human_observation.accident_loc
    for i, traffic_loc in enumerate(human_observation.traffic_locs):
        if traffic_loc[2] != -1:
            new_human_belief.traffic_locs[i][2] = float(traffic_loc[2])

    return new_ai_belief, new_human_belief
    
def bayesian_update(maze_problem, new_human_belief, costs_to_go, action):
    
    temp_belief = copy.deepcopy(new_human_belief)
    # find the traffic locations whose condition is uncertain
    unknown_traffic_locs = [(ind, loc) for ind, loc in enumerate(temp_belief.traffic_locs) if loc[2] not in {0.0, 1.0}]
    unknown_traffic_loc_states = list(product([0.0, 1.0], repeat=len(unknown_traffic_locs)))
    
    # for each possible state of the uncertain traffic locations, compute the posterior probability
    posteriors = []
    for unknown_traffic_loc_state in unknown_traffic_loc_states:
        
        # potential_traffic_locs is one possible state of the uncertain traffic locations
        potential_traffic_locs = copy.deepcopy(temp_belief.traffic_locs)
        for ind, loc in enumerate(unknown_traffic_locs):
            potential_traffic_locs[loc[0]][2] = unknown_traffic_loc_state[ind]

        # compute the prior probability of that particular state
        prior = 1
        for ind, x in enumerate(temp_belief.traffic_locs):
            # prior is the probability of potential_traffic_locs according to the human's belief
            prior *= potential_traffic_locs[ind][2]*x[2] + (1-potential_traffic_locs[ind][2])*(1-x[2])

        # compute the likelihood of the ai's action given the potential_traffic_locs
        potential_belief = copy.deepcopy(maze_problem.human_agent.belief)
        potential_belief.traffic_locs = potential_traffic_locs  # assumes the ai is planning given that particular state of traffic
        potential_belief.closure_loc = maze_problem.ai_agent.belief.closure_loc # NOTE: assumes the ai is planning without additional knowledge about the road closure
        action_logits = maze_problem.human_agent.get_action_logits(costs_to_go['human'][str(potential_traffic_locs)], potential_belief)
        likelihood = maze_problem.human_agent.policy_model.probability(action, action_logits, sim_scaler=maze_problem.sim_scaler)

        # baye's rule
        posteriors.append((likelihood * prior, potential_traffic_locs))

    # normalize the posteriors
    for i in range(len(temp_belief.traffic_locs)):
        post = 0
        temp_belief.traffic_locs[i][2] = 0
        for j in range(len(posteriors)):
            if posteriors[j][1][i][2] == 1:
                temp_belief.traffic_locs[i][2] += posteriors[j][0]
            post += posteriors[j][0]
        temp_belief.traffic_locs[i][2] /= post
        
        # NOTE: round the probabilities to 5 decimal places -- this is to avoid numerical errors when accessing costs_to_go['human']
        temp_belief.traffic_locs[i][2] = round(temp_belief.traffic_locs[i][2], 5)
        
    return temp_belief

def initialize_logs(maze_problem, logs):

    maze_map = copy.deepcopy(maze_problem.env.state.maze_map)
    maze_map[maze_map == '*'] = 1
    maze_map[maze_map == '-'] = 0
    maze_map = maze_map.astype(int).tolist()
    goal_loc = copy.deepcopy(maze_problem.env.state.goal_loc)
    closure_loc = copy.deepcopy(maze_problem.env.state.closure_loc)
    accident_loc = copy.deepcopy(maze_problem.env.state.accident_loc)
    traffic_locs = copy.deepcopy(maze_problem.env.state.traffic_locs)
    logs['maze_map'] = maze_map
    logs['goal_loc'] = goal_loc
    logs['closure_loc'] = closure_loc
    logs['accident_loc'] = accident_loc
    logs['traffic_locs'] = traffic_locs
    
def human_simulations(maze_problem, rng_agent, num_of_seeds=10, time_remaining=None):

    simulated_state = copy.deepcopy(maze_problem.env.state)

    # simulate future of the episode with human in control
    # details of the simulation:
    # - any committed action is erased
    # - accident and closure locations (if any) match the human's belief, not the true state
    # - traffic conditions are sampled from bernoullis based on the human's current belief
    # - agent switching is disabled
    # - the planning is done using the human's current belief about the traffic conditions
    simulated_state.agent_name = 'human'
    simulated_state.committed_action = 'none'   # any committed action is erased
    simulated_state.accident_loc = maze_problem.human_agent.belief.accident_loc # inside the simulation, the true state matches the human's belief
    simulated_state.closure_loc = maze_problem.human_agent.belief.closure_loc

    human_completion_times = []
    for seed in range(num_of_seeds):
        # for every simulation, the true traffic conditions are sampled from bernoullis based on the human's belief
        simulated_state.traffic_locs = [[traffic_x, traffic_y, rng_agent.binomial(1, traffic_prob)] for traffic_x, traffic_y, traffic_prob in maze_problem.human_agent.belief.traffic_locs]
        simulated_human_problem = MazeProblem.create(init_true_state=simulated_state, traffic_delay=maze_problem.traffic_delay, radius=maze_problem.radius, human_scaler=maze_problem.sim_scaler, \
                                            ai_scaler=maze_problem.sim_scaler, agent_seed=seed, ai_switching=0.0, human_switching=0.0, human_simulation_belief=maze_problem.human_agent.belief)
        human_logs = {}
        _ = simulate(simulated_human_problem, human_logs, verbose=0)
        human_completion_times.append(human_logs['length']-1)

    # NOTE: adding +1 to the average completion time if the driver changes
    # because the simulated episodes start one time step later
    if maze_problem.env.state.agent_name == 'ai':
        human_completion_times = [t+1 for t in human_completion_times]

    # simulate future of the episode with ai in control
    # details of the simulation:
    # - any committed action is kept as is
    # - accident and closure locations (if any) match the human's belief, not the true state
    # - traffic conditions are sampled from bernoullis based on the human's current belief
    # - agent switching is disabled
    # - the planning is done using the sampled traffic conditions
    # - the ai is assumed to follow a softmax policy with scaler same as the human
    simulated_state.agent_name = 'ai'
    simulated_state.committed_action = maze_problem.env.state.committed_action  # committed action is kept as is
    simulated_state.accident_loc = maze_problem.human_agent.belief.accident_loc # inside the simulation, the true state matches the human's belief
    simulated_state.closure_loc = maze_problem.human_agent.belief.closure_loc

    ai_completion_times = []
    for seed in range(num_of_seeds):
        # for every simulation, the true traffic conditions are sampled from bernoullis based on the human's belief
        simulated_state.traffic_locs = [[traffic_x, traffic_y, rng_agent.binomial(1, traffic_prob)] for traffic_x, traffic_y, traffic_prob in maze_problem.human_agent.belief.traffic_locs]
        ai_simulated_belief=copy.deepcopy(maze_problem.ai_agent.belief)
        # the planning is done using the sampled traffic conditions
        ai_simulated_belief.traffic_locs = copy.deepcopy(simulated_state.traffic_locs)
        # the ai is assummed to follow a softmax policy with scaler same as the human
        simulated_human_problem = MazeProblem.create(init_true_state=simulated_state, traffic_delay=maze_problem.traffic_delay, radius=maze_problem.radius, human_scaler=maze_problem.sim_scaler, \
                                        ai_scaler=maze_problem.sim_scaler, agent_seed=seed, ai_switching=0.0, human_switching=0.0, ai_simulation_belief=ai_simulated_belief)
        ai_logs = {}
        _ = simulate(simulated_human_problem, ai_logs, verbose=0)
        ai_completion_times.append(ai_logs['length']-1)

    # NOTE: adding +1 to the average completion time if the driver changes
    # because the simulated episodes start one time step later
    if maze_problem.env.state.agent_name == 'human':
        ai_completion_times = [t+1 for t in ai_completion_times]

    if time_remaining is None:
        # set AI and human scores as the negative average completion times
        ai_score = - np.mean(ai_completion_times)
        human_score = - np.mean(human_completion_times)
    else:
        # set AI and human scores as the probability of reaching the goal within the horizon
        ai_score = np.mean(np.array(ai_completion_times) <= time_remaining)
        human_score = np.mean(np.array(human_completion_times) <= time_remaining)

    return ai_score, human_score

def simulate(maze_problem, logs, verbose=0, override=False, given_responses=None, counterfactual_seed=None, counterfactual_ai_scaler=None, counterfactual_human_scaler=None, horizon=None, human_prob_estimates_file=None):

    # initialization
    initialize_logs(maze_problem, logs)
    rng_agent = default_rng(seed=maze_problem.agent_seed)
    # initialize the object where the user's responses to the prompts are stored in the case of override
    record_responses = []
    # initialize all tiles as unexplored, except for the ones in the field of vision of the vehicle
    tiles_explored = np.zeros(maze_problem.env.state.maze_map.shape, dtype=int).tolist()
    update_explored_tiles(maze_problem, tiles_explored, maze_problem.env.state.vehicle_loc)
    switching_disabled = False # this is to disable further switching after they have switched once

    costs_to_go = plan(maze_problem)

    logs['time_steps'] = []
    t=0
    while maze_problem.env.state.vehicle_loc != maze_problem.env.state.goal_loc:
        
        if verbose>0:
            print("========== Step %d ==========" % (t+1))
            
        # check if the current vehicle_loc is a traffic location
        is_in_traffic = False
        for traffic_x, traffic_y, traffic_bool in maze_problem.env.state.traffic_locs:
            if maze_problem.env.state.vehicle_loc == [traffic_x, traffic_y] and traffic_bool == 1:
                is_in_traffic = True
                break
        
        # get next action depending on which agent is currently in control
        if maze_problem.env.state.agent_name == 'ai':
            # the ai moves on the shortest path given the current traffic conditions
            action = maze_problem.ai_agent.act(costs_to_go['ai'][str(maze_problem.ai_agent.belief.traffic_locs)], rng_agent, maze_problem.env.state.committed_action, is_in_traffic)
            codriver_action = maze_problem.human_agent.act(costs_to_go['human'][str(maze_problem.human_agent.belief.traffic_locs)], rng_agent, maze_problem.env.state.committed_action, is_in_traffic)
            if override and not switching_disabled:
                if verbose > 0:
                    print("Current state:\n", maze_problem.env.state)
                    print("Action:", action)

                if given_responses is not None:
                    # read prompt response from file
                    prompt = given_responses.pop(0)
                else:
                    # read prompt response from keyboard input and record it
                    prompt = input('Should the AI offer control to the human? (y/n)\n')
                    record_responses.append(prompt)
                
                if prompt == 'y':
                    if len(action.dir)==1:
                        action.dir += 'c'
                else:
                    if len(action.dir)==2:
                        action.dir = action.dir[0]
        elif maze_problem.env.state.agent_name == 'human':
            # the human moves on the shortest expected path given their current belief about the traffic conditions 
            action = maze_problem.human_agent.act(costs_to_go['human'][str(maze_problem.human_agent.belief.traffic_locs)], rng_agent, maze_problem.env.state.committed_action, is_in_traffic)
            codriver_action = maze_problem.ai_agent.act(costs_to_go['ai'][str(maze_problem.ai_agent.belief.traffic_locs)], rng_agent, maze_problem.env.state.committed_action, is_in_traffic)
            if override and not switching_disabled:
                if verbose > 0:
                    print("Current state:\n", maze_problem.env.state)
                    print("Action:", action)

                if given_responses is not None:
                    # read prompt response from file
                    prompt = given_responses.pop(0)
                else:
                    # read prompt response from keyboard input and record it
                    prompt = input('Should the AI ask to take control? (y/n)\n')
                    record_responses.append(prompt)
                
                if prompt == 'y':
                    if len(action.dir)==1:
                        action.dir += 'c'
                else:
                    if len(action.dir)==2:
                        action.dir = action.dir[0]

        if action is None:
            if verbose > 0:
                print('No feasible plan after time step %d' % t)
                print('Terminating early')
            
            logs['length'] = t
            return
        
        # update the logs with time step information
        update_logs(logs, maze_problem, action, codriver_action, tiles_explored, t)
        
        # bayesian update of the human's belief about the traffic conditions, based on the direction that the ai is planning to follow
        belief_changed = False
        if maze_problem.env.state.agent_name == 'ai':
            belief_action = copy.deepcopy(action)
            belief_action.dir = belief_action.dir[0]
            bayesian_human_belief = bayesian_update(maze_problem, maze_problem.human_agent.belief, costs_to_go, belief_action)
            # this is to avoid numerical errors
            if not np.allclose(np.array(maze_problem.human_agent.belief.traffic_locs), np.array(bayesian_human_belief.traffic_locs)):
                belief_changed = True
                maze_problem.human_agent.set_belief(bayesian_human_belief)

        # agent switching mechanism
        if action.dir in {'uc', 'dc', 'lc', 'rc'}:
            
            if human_prob_estimates_file is None:
                # perform human-ai simulations and compute the average completion times
                ai_score, human_score = human_simulations(maze_problem, rng_agent, num_of_seeds=300, time_remaining=horizon-t)
            else:
                try:
                    with open(human_prob_estimates_file, 'r') as f:
                        human_prob_estimates = json.load(f)
                        ai_score = human_prob_estimates['ai_score']
                        human_score = human_prob_estimates['human_score']
                except:
                    # perform human-ai simulations and compute the average completion times
                    ai_score, human_score = human_simulations(maze_problem, rng_agent, num_of_seeds=300, time_remaining=horizon-t)
                    # save the scores to a file
                    with open(human_prob_estimates_file, 'w') as f:
                        json.dump({'ai_score': ai_score, 'human_score': human_score}, f, cls=NpEncoder)
            
            # the agent decides to taker over or confirm the ai's direction by sampling from a softmax policy
            logits = [maze_problem.sim_scaler * ai_score, maze_problem.sim_scaler * human_score]    # NOTE: sim_scaler temperature is set independently from the agents' policy scalers
            softmax_scores = np.exp(logits) / np.sum(np.exp(logits))
            choice = rng_agent.choice(a=['ai', 'human'], p=softmax_scores)
            if maze_problem.env.state.agent_name == 'ai' and override:

                if given_responses is not None:
                    # read prompt response from file
                    prompt = given_responses.pop(0)
                else:
                    # NOTE: the following lines are for testing, they help to see how good each one of the two decisions is
                    # print('Logit for the human: %f' % human_score)
                    # print('Logit for the ai: %f' % ai_score)
                    # print(maze_problem.human_agent.belief.traffic_locs)

                    # read prompt response from keyboard input and record it
                    prompt = input('Should the human take over? (y/n)\n')
                    record_responses.append(prompt)

                if prompt == 'y':
                    choice = 'human'
                    start_counterfactual = False
                elif prompt == 'n':
                    choice = 'ai'
                    start_counterfactual = False
                elif prompt == 'ycf':
                    choice = 'human'
                    start_counterfactual = True
                elif prompt == 'ncf':
                    choice = 'ai'
                    start_counterfactual = True
                
            elif maze_problem.env.state.agent_name == 'human' and override:
                
                if given_responses is not None:
                    # read prompt response from file
                    prompt = given_responses.pop(0)
                else:
                    # NOTE: the following lines are for testing, they help to see how good each one of the two decisions is
                    # print('Logit for the human: %f' % human_score)
                    # print('Logit for the ai: %f' % ai_score)
                    # print(maze_problem.human_agent.belief.traffic_locs)

                    # read prompt response from keyboard input and record it
                    prompt = input('Should the AI take over? (y/n)\n')
                    record_responses.append(prompt)
                
                if prompt == 'y':
                    choice = 'ai'
                    start_counterfactual = False
                elif prompt == 'n':
                    choice = 'human'
                    start_counterfactual = False
                elif prompt == 'ycf':
                    choice = 'ai'
                    start_counterfactual = True
                elif prompt == 'ncf':
                    choice = 'human'
                    start_counterfactual = True


            if maze_problem.env.state.agent_name != choice:
                # if the chosen and the current agents are different, the state remains
                # the same, no commited action is set, and the agent changes
                next_state = copy.deepcopy(maze_problem.env.state)
                next_state.time_idle += 1
                next_state.committed_action = 'none'
                next_state.agent_name = choice
                reward = maze_problem.env.reward_model.sample(maze_problem.env.state, next_state)
                # no further switching after the first switch
                maze_problem.human_agent.set_switching_off()
                maze_problem.ai_agent.set_switching_off()
                switching_disabled = True
            else:
                # if the chosen and the current agents are the same, the commited action applies
                action.dir = action.dir[0]
                # compute next state and reward
                next_state = maze_problem.env.transition_model.sample(maze_problem.env.state, action)
                reward = maze_problem.env.reward_model.sample(maze_problem.env.state, next_state)

            if start_counterfactual:
                # no further switching in counterfactual simulations
                maze_problem.human_agent.set_switching_off()
                maze_problem.ai_agent.set_switching_off()
                switching_disabled = True
                # change the agent seed and scalers
                rng_agent = default_rng(seed=counterfactual_seed)
                maze_problem.human_agent.policy_model.set_scaler(counterfactual_human_scaler)
                maze_problem.ai_agent.policy_model.set_scaler(counterfactual_ai_scaler)

        else:
            # compute next state and reward
            next_state = maze_problem.env.transition_model.sample(maze_problem.env.state, action)
            reward = maze_problem.env.reward_model.sample(maze_problem.env.state, next_state)

        # get observation from the environment
        ai_observation = maze_problem.ai_agent.observation_model.sample(next_state)
        human_observation = maze_problem.human_agent.observation_model.sample(next_state)

        # print time step information and apply transition
        time_step_printing(verbose, t, maze_problem, action, next_state, reward, ai_observation, human_observation)
        maze_problem.env.apply_transition(next_state)
        
        # update the explored tiles
        update_explored_tiles(maze_problem, tiles_explored, next_state.vehicle_loc)

        # add observations to the agents' histories
        maze_problem.ai_agent.update_history(action, ai_observation)
        maze_problem.human_agent.update_history(action, human_observation)
        
        # update the agents' beliefs
        new_ai_belief, new_human_belief = update_beliefs(maze_problem, ai_observation, human_observation)
        
        if new_ai_belief.accident_loc != maze_problem.ai_agent.belief.accident_loc or \
            new_human_belief.accident_loc != maze_problem.human_agent.belief.accident_loc or \
            new_ai_belief.closure_loc != maze_problem.ai_agent.belief.closure_loc or \
            new_human_belief.closure_loc != maze_problem.human_agent.belief.closure_loc or \
            new_ai_belief.traffic_locs != maze_problem.ai_agent.belief.traffic_locs or \
            new_human_belief.traffic_locs != maze_problem.human_agent.belief.traffic_locs or \
            belief_changed:
            if verbose==2:
                print(
                """
                **************************************
                *********** Belief updated ***********
                **************************************
                """)
            maze_problem.ai_agent.set_belief(new_ai_belief)
            maze_problem.human_agent.set_belief(new_human_belief)    
            costs_to_go = plan(maze_problem)
        else:
            maze_problem.ai_agent.set_belief(new_ai_belief)
            maze_problem.human_agent.set_belief(new_human_belief)
        t += 1

    # update the logs with the last time step information
    update_logs(logs, maze_problem, action, codriver_action, tiles_explored, t)
    if verbose:
        print('Goal reached in %d steps' % t)
    logs['length'] = t+1

    # return the user keyboard responses to the prompts (if any)
    return record_responses

@click.command()
@click.option('--log_file', type=str, required=True, help='Directory where to place the trajectory logs')
@click.option('--world_file', type=str, required=True, help='World to use')
@click.option('--traffic_delay', type=int, default=10, help='Time penalty for crossing a traffic location')
@click.option('--human_scaler', type=float, default=None, help="Scaler for the human agent's softmax policy")
@click.option('--ai_scaler', type=float, default=None, help="Scaler for the ai agent's softmax policy")
@click.option('--ai_switching', type=float, default=0.0, help='Probability of AI suggesting to switch control')
@click.option('--human_switching', type=float, default=0.0, help='Probability of human suggesting to switch control')
@click.option('--radius', type=int, default=1, help='The radius of the rectangular field of view')
@click.option('--agent_seed', type=int, default=42, help='Random seed for the agent policy')
@click.option('--verbose', type=click.Choice(['0', '1', '2']), default='0', help='Select level of verbosity')
@click.option('--sim_scaler', type=float, default=1.0, help="Scaler for the human's simulations")
@click.option('--initial_agent', type=str, default='ai', help="Initial agent ('ai' or 'human')")
@click.option('--override', is_flag=True, default=False, help='If true, the switching prompts and the human responses are set manually by the user')
@click.option('--responses_file', type=str, default=None, help='If set, the user responses to the prompts are stored in a file')
@click.option('--semi_manual_seed', type=int, default=None, help='Seed for the factual part of a semi-counterfactual episode')
@click.option('--horizon', type=int, default=None, help='Horizon (time limit) of the episode')
@click.option('--human_prob_estimates_file', type=str, default=None, help='File where the human and ai scores are stored, serves as cache')
def execute_episode(log_file, world_file, traffic_delay, human_scaler, ai_scaler, ai_switching, human_switching, radius, agent_seed, verbose, sim_scaler, initial_agent, override, responses_file, semi_manual_seed, horizon, human_prob_estimates_file):
    
    verbose = int(verbose)
    if override:
        # check if the file store_responses_file exists and read the responses
        try:
            with open(responses_file, 'rb') as f:
                given_responses = pkl.load(f)
                record_responses = []
        except FileNotFoundError:
            given_responses = None
            record_responses = []
        
        if given_responses is not None:
            # read prompt response from file
            prompt = given_responses.pop(0)
        else:
            # read prompt response from keyboard input and record it
            prompt = input('Who is the initial agent (ai/human)?\n')
            while prompt not in {'ai', 'human'}:
                prompt = input('Incorrect input. Please type either ai or human.\n')
            record_responses.append(prompt)
        
        if prompt == 'ai':
            initial_agent = 'ai'
        else:
            initial_agent = 'human'
    else:
        # if override is false, these variables are not important, however, they need to be initialized
        given_responses = None
        record_responses = []
    
    init_true_state = MazeState(*parse_initial_state(world_file, initial_agent))
    if semi_manual_seed is None:
        maze_problem = MazeProblem.create(init_true_state=init_true_state, agent_seed=agent_seed, traffic_delay=traffic_delay, radius=radius, human_scaler=human_scaler, \
                                ai_scaler=ai_scaler, ai_switching=ai_switching, human_switching=human_switching, sim_scaler=sim_scaler)
    else:
        maze_problem = MazeProblem.create(init_true_state=init_true_state, agent_seed=semi_manual_seed, traffic_delay=traffic_delay, radius=radius, human_scaler=None, \
                                ai_scaler=None, ai_switching=ai_switching, human_switching=human_switching, sim_scaler=sim_scaler)
    
    # simulate the episode
    logs = {}
    simulation_responses = simulate(maze_problem=maze_problem, logs=logs, verbose=verbose, override=override, given_responses=given_responses, counterfactual_seed=agent_seed, \
                                    counterfactual_ai_scaler=ai_scaler, counterfactual_human_scaler=human_scaler, horizon=horizon, human_prob_estimates_file=human_prob_estimates_file)
    record_responses = record_responses + simulation_responses

    def remove_suffix(input_string, suffix):
        if suffix and input_string.endswith(suffix):
            return input_string[:-len(suffix)]
        return input_string

    # save logs to file
    if override:
        if given_responses is not None:
            # read prompt response from file
            special = given_responses.pop(0)
        else:
            # read prompt response from keyboard input and record it
            special = input('Give a single word to mark what is special about this episode: ')
            while special == '':
                special = input('Please give a non-empty word: ')
            record_responses.append(special)
        log_file = remove_suffix(log_file, '.json') + '_initagent:' + initial_agent + '_explanation:' + special + '.json'
        responses_file = remove_suffix(responses_file, '.pkl') + '_explanation:' + special + '.pkl'

    if override and given_responses is None:
        # save the keyboard input responses to the file
        with open(responses_file, 'wb') as f:
            pkl.dump(record_responses, f)

    with open(log_file, 'w') as f:
        json.dump(logs, f, cls=NpEncoder)
    
if __name__ == '__main__':
    # NOTE: the following commented line is only for testing purposes
    # execute_episode(log_file='test.json', world_file='data/worlds/world_1.txt', traffic_delay=10, human_scaler=None, ai_scaler=None, ai_switching=0.0, human_switching=0.5, \
    #             radius=1, agent_seed=42, verbose=1, initial_agent='human', sim_scaler=1.0, override=False)
    execute_episode()
