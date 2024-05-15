import pomdp_py
from domain import MazeObservation, MazeAction
import copy
import numpy as np

# Observation model
class ObservationModel(pomdp_py.ObservationModel):
    def __init__(self, radius=1, agent_name='human'):
        self.radius = radius
        self.agent_name = agent_name

    def _is_in_field_of_vision(self, v_loc, loc):
        return (v_loc[0]-1 <= loc[0] <= v_loc[0]+1) and (v_loc[1]-1 <= loc[1] <= v_loc[1]+1)

    def get_field_of_vision(self, v_loc):
        field_of_vision = []
        for i in range(v_loc[0]-1, v_loc[0]+2):
            for j in range(v_loc[1]-1, v_loc[1]+2):
                field_of_vision.append([i, j])
        return field_of_vision

    def _get_observation(self, next_state):
        v_loc = next_state.vehicle_loc
        # if closure is in the field of vision or agent is human, then add it to the observation
        if self._is_in_field_of_vision(v_loc, next_state.closure_loc) or self.agent_name == 'human':
            closure_loc = next_state.closure_loc
        else:
            closure_loc = [-1, -1]  # no closure in the field of vision

        # accident are unknown to both the human and ai, unless they are in the field of vision
        if self._is_in_field_of_vision(v_loc, next_state.accident_loc):
            accident_loc = next_state.accident_loc
        else:
            accident_loc = [-1, -1] # no accident in the field of vision
        
        traffic_locs = []
        for traffic_x, traffic_y, traffic_bool in next_state.traffic_locs:
            # if traffic spot is in the field of vision or agent is AI, then add it to the observation
            if self._is_in_field_of_vision(v_loc, [traffic_x, traffic_y]) or self.agent_name == 'ai':
                traffic_locs.append([traffic_x, traffic_y, traffic_bool])
            else:
                traffic_locs.append([traffic_x, traffic_y, -1])   # traffic spot not in field of vision

        return MazeObservation(closure_loc, accident_loc, traffic_locs)

    def probability(self, observation, next_state):
        
        if observation == self._get_observation(next_state):
            return 1.0
        else:
            return 0.0

    def sample(self, next_state):
        
        return self._get_observation(next_state)


# Transition Model
class TransitionModel(pomdp_py.TransitionModel):

    def __init__(self, traffic_delay=10, human_penalty=0):
        self.traffic_delay = traffic_delay
        self.human_penalty = human_penalty  # NOTE: need to set the default value higher (e.g., 1) if we want the human to be slower

    def _is_stuck_in_traffic(self, v_loc, traffic_locs):
        
        for traffic_loc in traffic_locs:
            if traffic_loc == [v_loc[0], v_loc[1], 1]:
                return True
        
        return False
    
    def _get_candidate_v_loc(self, v_loc, action):
        if action.dir == 'r':
            return v_loc[0], v_loc[1]+1
        elif action.dir == 'l':
            return v_loc[0], v_loc[1]-1
        elif action.dir == 'u':
            return v_loc[0]-1, v_loc[1]
        elif action.dir == 'd':
            return v_loc[0]+1, v_loc[1]
        
    def get_next_state(self, state, action):
        
        if action.dir == 'rc' or action.dir == 'lc' or action.dir == 'uc' or action.dir == 'dc':
            # stay in the same tile, ask to switch control and commit to next action
            next_state = copy.deepcopy(state)
            next_state.time_idle += 1
            next_state.committed_action = action.dir[0]
            return next_state
        
        v_loc = state.vehicle_loc
        stuck = self._is_stuck_in_traffic(v_loc, state.traffic_locs)
        
        if stuck and (state.time_idle < self.traffic_delay + (state.agent_name == 'human') * self.human_penalty):
            # stuck in traffic
            next_state = copy.deepcopy(state)
            next_state.time_idle += 1
        elif state.agent_name == 'human' and state.time_idle < self.human_penalty:
            # human needs additional time before moving to another tile
            next_state = copy.deepcopy(state)
            next_state.time_idle += 1
        else:
            
            # try to move in the direction of the action
            candidate_v_loc = self._get_candidate_v_loc(v_loc, action)
            is_in_map_boundaries = (0 <= candidate_v_loc[0] < state.maze_map.shape[0]) and (0 <= candidate_v_loc[1] < state.maze_map.shape[1])
            
            # out of bounds --or-- going on a wall --or-- going on an accident --or-- going on a road closure
            if (not is_in_map_boundaries) or (state.maze_map[candidate_v_loc] == '*') or (state.accident_loc == list(candidate_v_loc)) or (state.closure_loc == list(candidate_v_loc)):
                # cannot move that way
                next_state = copy.deepcopy(state)
                next_state.time_idle += 1
            else:
                next_state = copy.deepcopy(state)
                next_state.vehicle_loc = list(candidate_v_loc)
                next_state.time_idle = 0

        next_state.committed_action = 'none'
        return next_state

    def probability(self, next_state, state, action):
        """According to problem spec, the world resets once
        action is open-left/open-right. Otherwise, stays the same"""
        
        if next_state == self.get_next_state(state, action):
            return 1.0
        else:
            return 0.0

    def sample(self, state, action):
        return(self.get_next_state(state, action))

# Reward Model
class RewardModel(pomdp_py.RewardModel):
    def _reward_func(self, state, next_state):
        
        if (state.vehicle_loc != state.goal_loc) and (next_state.vehicle_loc == next_state.goal_loc):
            return 100
        else:
            return -1
    
    def sample(self, state, next_state):
        # deterministic
        return self._reward_func(state, next_state)

# Policy Model
class PolicyModel(pomdp_py.RolloutPolicy):
    """
    A simple policy model that takes the optimal action
    or a random action with probability random_choice
    """
    ACTIONS = [MazeAction(dir)
              for dir in ['r', 'l', 'u', 'd']]

    def __init__(self, scaler=1.0, switching=0.0):
        self.scaler = scaler
        self.switching = switching

    def probability(self, action, action_logits, committed_action='none', sim_scaler=None):
        
        # agent is committed to a certain action
        if committed_action != 'none':
            if action.dir == committed_action:
                return 1.0
            else:
                return 0.0

        no_switching_action = copy.deepcopy(action)
        no_switching_action.dir = no_switching_action.dir[0]
        
        # sim_scaler is not None when the human is mentally simulating
        if sim_scaler is not None:
            # probability equals the respective softmax score
            logits = [-sim_scaler*x[1] for x in action_logits]
            softmax_scores = np.exp(logits) / np.sum(np.exp(logits))
            for i, a in enumerate(action_logits):
                if a[0] == no_switching_action:
                    return softmax_scores[i]

        # scaler is None when the AI is driving
        if self.scaler is not None:
            # probability equals the respective softmax score
            logits = [-self.scaler*x[1] for x in action_logits]
            softmax_scores = np.exp(logits) / np.sum(np.exp(logits))
            for i, a in enumerate(action_logits):
                if a[0] == no_switching_action:
                    return softmax_scores[i]
        else:
            # ai always performs optimally
            if no_switching_action == min(action_logits, key=lambda x: x[1])[0]:
                return 1.0
            else:
                return 0.0
        
        return
    
    def sample(self, action_logits, rng_agent, committed_action='none', is_in_traffic=False):
        
        if committed_action != 'none':
            return MazeAction(committed_action)

        # scaler is None when the AI is driving
        if self.scaler is not None:
            # sample action from action_logits based on softmax of the second element
            logits = [-self.scaler*x[1] for x in action_logits]
            softmax_scores = np.exp(logits) / np.sum(np.exp(logits))
            next_action = rng_agent.choice(action_logits, p=softmax_scores)[0]
        else:
            # ai performs optimally and chooses the action by picking the one with the minimum logit
            next_action = min(action_logits, key=lambda x: x[1])[0]

            # propose to switch control with probability switching
            if rng_agent.random() < self.switching and not is_in_traffic:
                next_action.dir += 'c'

        return next_action
    
    def set_scaler(self, scaler):
        self.scaler = scaler