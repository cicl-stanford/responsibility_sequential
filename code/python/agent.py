"""Implementation of the basic policy tree based value iteration as explained
in section 4.1 of `Planning and acting in partially observable stochastic
domains` :cite:`kaelbling1998planning`

Warning: No pruning - the number of policy trees explodes very fast.
"""

from pomdp_py.framework.basics import Agent
import numpy as np
from domain import MazeAction

class CompactBelief():

    def __init__(self, maze_map, vehicle_loc, goal_loc, traffic_locs, accident_loc=[-1, -1], closure_loc=[-1, -1], time_idle=0):
        
        self.maze_map = maze_map
        self.vehicle_loc = vehicle_loc
        self.goal_loc = goal_loc
        self.accident_loc = accident_loc
        self.closure_loc = closure_loc
        self.traffic_locs = traffic_locs
        self.time_idle = time_idle

    def __hash__(self):
        return hash(str(self).split('_idle')[0])
    def __eq__(self, other):
        if isinstance(other, CompactBelief):
            return str(self) == str(other)
        return False
    def __str__(self):
        return "maze_%s_vehicle_%s_goal_%s_closure_%s_accident_%s_traffics_%s_idle_%s" % (np.array2string(self.maze_map), str(self.vehicle_loc),\
                                                str(self.goal_loc), str(self.closure_loc), str(self.accident_loc),\
                                                str(self.traffic_locs), str(self.time_idle))
    def __repr__(self):
        return "CompactBelief: %s" % str(self)

class LazyAgent(Agent):

    def __init__(self, init_belief,
                 policy_model,
                 transition_model=None,
                 observation_model=None,
                 reward_model=None,
                 agent_name = 'ai'):
        self._init_belief = init_belief
        self._policy_model = policy_model

        self._transition_model = transition_model
        self._observation_model = observation_model
        self._reward_model = reward_model
        self._agent_name = agent_name

        # For online planning
        self._cur_belief = init_belief
        self._history = ()

    @property
    def history(self):
        """history(self)
        Current history."""
        # history are of the form ((a,o),...);
        return self._history

    def update_history(self, real_action, real_observation):
        """update_history(self, real_action, real_observation)"""
        self._history += ((real_action, real_observation),)

    @property
    def init_belief(self):
        """
        init_belief(self)
        Initial belief distribution."""
        return self._init_belief

    @property
    def belief(self):
        """
        belief(self)
        Current belief distribution."""
        return self.cur_belief

    @property
    def cur_belief(self):
        return self._cur_belief

    def set_belief(self, belief, prior=False):
        """set_belief(self, belief, prior=False)"""
        self._cur_belief = belief
        if prior:
            self._init_belief = belief

    def sample_belief(self):
        """sample_belief(self)
        Returns a state (:class:`State`) sampled from the belief."""
        return self._cur_belief.random()

    @property
    def agent_name(self):
        return self._agent_name

    @property
    def observation_model(self):
        return self._observation_model

    @property
    def transition_model(self):
        return self._transition_model

    @property
    def reward_model(self):
        return self._reward_model

    @property
    def policy_model(self):
        return self._policy_model

    def _get_candidate_v_loc(self, v_loc, action):
        if action == 'r':
            return v_loc[0], v_loc[1]+1
        elif action == 'l':
            return v_loc[0], v_loc[1]-1
        elif action == 'u':
            return v_loc[0]-1, v_loc[1]
        elif action == 'd':
            return v_loc[0]+1, v_loc[1]
    
    def _get_neighbors(self, node, belief):
        ACTIONS = ['r', 'l', 'u', 'd']
        
        adjacent_locs = []
        for action in ACTIONS:
            candidate_v_loc = self._get_candidate_v_loc(node, action)
            is_in_map_boundaries = (0 <= candidate_v_loc[0] < belief.maze_map.shape[0]) and (0 <= candidate_v_loc[1] < belief.maze_map.shape[1])
            if (is_in_map_boundaries) and (belief.maze_map[candidate_v_loc] == '-') and (list(candidate_v_loc) != belief.closure_loc) and (list(candidate_v_loc) != belief.accident_loc):
                adjacent_locs.append((action, list(candidate_v_loc)))

        return adjacent_locs
    
    def get_action_logits(self, costs_to_go, potential_belief=None):
        # choose the next action based on the agent's policy
        
        if potential_belief is not None:
            belief = potential_belief
        else:
            belief = self.belief
        
        vehicle_loc = belief.vehicle_loc

        # if there is no feasible path from the current node, str(belief) will not be in costs_to_go
        if str(vehicle_loc) not in costs_to_go:
            return None
        
        adjacent_locs = self._get_neighbors(vehicle_loc, belief)
        action_logits = []
        for action, adjacent_loc in adjacent_locs:
            action_logits.append((MazeAction(action), costs_to_go[str(adjacent_loc)]))
        
        return action_logits

    def act(self, costs_to_go, rng_agent, committed_action, is_in_traffic=False):
        
        action_logits = self.get_action_logits(costs_to_go)
        return self.policy_model.sample(action_logits, rng_agent, committed_action, is_in_traffic)

    def set_switching_off(self):
        self.policy_model.switching = 0

    def update_policy(self, policy_model):
        """update_policy(self, policy_model)
        Updates the policy model of the agent."""
        self._policy_model = policy_model
