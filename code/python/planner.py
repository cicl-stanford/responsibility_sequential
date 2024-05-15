import heapq

class Planner:

    def __init__(self, maze_map, goal_loc, accident_loc, closure_loc, traffic_locs, traffic_delay, agent_name):
        self.maze_map = maze_map
        self.goal_loc = goal_loc
        self.accident_loc = accident_loc
        self.closure_loc = closure_loc
        self.traffic_locs = traffic_locs
        self.traffic_delay = traffic_delay
        self.agent_name = agent_name

    def _get_candidate_v_loc(self, v_loc, action):
        if action == 'r':
            return v_loc[0], v_loc[1]+1
        elif action == 'l':
            return v_loc[0], v_loc[1]-1
        elif action == 'u':
            return v_loc[0]-1, v_loc[1]
        elif action == 'd':
            return v_loc[0]+1, v_loc[1]
    
    def _compute_edge_cost(self, n1, n2):
        
        if self.agent_name == 'ai':
            base_cost = 1
        elif self.agent_name == 'human':
            base_cost = 1   # NOTE: need to set this higher (e.g., 2) if we want the human to be slower
        
        current_traffic_spot = [-1, -1, -1]
        for traffic_loc in self.traffic_locs:
            if n1 == traffic_loc[:2]:
                current_traffic_spot = traffic_loc
        
        if (current_traffic_spot[0] == -1):
            # n1 is not a known traffic spot
            return base_cost    
        else:
            # n1 is a known traffic spot and the planner knows whether there is traffic or not
            return base_cost + int(self.traffic_delay)*current_traffic_spot[2]

    def _get_neighbors(self, node):
        ACTIONS = ['r', 'l', 'u', 'd']
        
        adjacent_locs = []
        for action in ACTIONS:
            candidate_v_loc = self._get_candidate_v_loc(node, action)
            is_in_map_boundaries = (0 <= candidate_v_loc[0] < self.maze_map.shape[0]) and (0 <= candidate_v_loc[1] < self.maze_map.shape[1])
            if (is_in_map_boundaries) and (self.maze_map[candidate_v_loc] == '-') and (list(candidate_v_loc) != self.closure_loc) and (list(candidate_v_loc) != self.accident_loc):
                adjacent_locs.append(list(candidate_v_loc))
        
        next_nodes = []
        for loc in adjacent_locs:
            edge_cost = self._compute_edge_cost(loc, node)
            next_nodes.append((loc, edge_cost))

        return next_nodes

    def dijkstra(self):

        # NOTE: Here, nodes should be 2-element coordinate lists [x, y]

        # Initialize the cost-to-go dictionary with infinite costs for all nodes except the goal node
        cost_to_go = {str(self.goal_loc): 0}
        
        # Initialize the priority queue with the goal node
        counter = 0
        heap = [(0, counter, self.goal_loc)]
        
        while heap:
            # Get the node with the smallest cost-to-go from the priority queue
            current_cost, _, current_node = heapq.heappop(heap)
            
            # If the current cost is greater than the cost-to-go for this node, skip it
            if current_cost > cost_to_go[str(current_node)]:
                continue
            
            # Update the cost-to-go for each neighbor of the current node
            for neighbor, edge_cost in self._get_neighbors(current_node):
                new_cost = edge_cost + cost_to_go[str(current_node)]
                if str(neighbor) not in cost_to_go:
                    cost_to_go[str(neighbor)] = float('inf')
                if new_cost < cost_to_go[str(neighbor)]:
                    cost_to_go[str(neighbor)] = new_cost
                    counter += 1
                    heapq.heappush(heap, (new_cost, counter, neighbor))
        
        return cost_to_go
