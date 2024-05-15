import pomdp_py
import numpy as np

class MazeState(pomdp_py.State):
    """
    state space:
        maze_map: n*n array of roads and obstacles
        position of vehicle: [int, int]
        position of goal: [int, int]
        position of road closure [int, int]
        position of accident: [int, int]
        positions of traffic: array of fixed size with elements [int, int, bool]
        time the vehicle has been idle: int
        identity of the agent driving: str | 'human' or 'ai'
        committed to action: str | 'l', 'r', 'u', 'd', 'none'
    """
    def __init__(self, maze_map, vehicle_loc, goal_loc, closure_loc, accident_loc, traffic_locs, time_idle, agent_name='ai', committed_action='none'):
        self.maze_map = maze_map
        self.vehicle_loc = vehicle_loc
        self.goal_loc = goal_loc
        self.closure_loc = closure_loc
        self.accident_loc = accident_loc
        self.traffic_locs = traffic_locs
        self.time_idle = time_idle
        self.agent_name = agent_name
        self.committed_action = committed_action
    def __hash__(self):
        return hash(str(self))
    def __eq__(self, other):
        if isinstance(other, MazeState):
            return str(self) == str(other)
        return False
    def __str__(self):
        print_map = self.maze_map.copy()
        print_map[self.vehicle_loc[0], self.vehicle_loc[1]] = 'v'
        print_map[self.goal_loc[0], self.goal_loc[1]] = 'g'
        if self.closure_loc[0] != -1:
            print_map[self.closure_loc[0], self.closure_loc[1]] = 'c'
        if self.accident_loc[0] != -1:
            print_map[self.accident_loc[0], self.accident_loc[1]] = 'a'
        for traffic_loc in self.traffic_locs:
            if traffic_loc[2] == 0:
                print_map[traffic_loc[0], traffic_loc[1]] = 't'
            else:
                print_map[traffic_loc[0], traffic_loc[1]] = 'T'
        
        return "%s_vehicle_%s_goal_%s_closure_%s_accident_%s_traffics_%s_idle_%s_agent_%s_committed_%s" % (np.array2string(print_map), str(self.vehicle_loc),\
                                                str(self.goal_loc), str(self.closure_loc), str(self.accident_loc),\
                                                str(self.traffic_locs), str(self.time_idle), self.agent_name, self.committed_action)
    def __repr__(self):
        return "MazeState: %s" % str(self)

class MazeAction(pomdp_py.Action):
    def __init__(self, dir):
        self.dir = dir
    def __hash__(self):
        return hash(self.dir)
    def __eq__(self, other):
        if isinstance(other, MazeAction):
            return self.dir == other.dir
        return False
    def __str__(self):
        return self.dir
    def __repr__(self):
        return "MazeAction: %s" % str(self)

class MazeObservation(pomdp_py.Observation):
    def __init__(self, closure_loc, accident_loc, traffic_locs):
        self.closure_loc = closure_loc
        self.accident_loc = accident_loc
        self.traffic_locs = traffic_locs
    def __hash__(self):
        return hash(str(self))
    def __eq__(self, other):
        if isinstance(other, MazeObservation):
            return str(self) == str(other)
        return False
    def __str__(self):
        return "closure_%s_accident_%s_traffics_%s" % (str(self.closure_loc), str(self.accident_loc), str(self.traffic_locs))
    def __repr__(self):
        return "MazeObservation: %s" % self.name