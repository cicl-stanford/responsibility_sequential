"""This file has some examples of world string."""
import numpy as np
import click
import os
import json

# all the info about a world are initially in the maze_map string
# v corresponds to the vehicle location
# g corresponds to the goal location
# t and T correspond to traffic locations, where T denotes that the traffic location is active
# a corresponds to an accident location
# c corresponds to a road closure location
# _ corresponds to a road
# * corresponds to an obstacle
# agent_name indicates who is the initial agent ('human' or 'ai')
# example_world = """
#     * * * * * * * * * g
#     * * * * * * * - - -
#     * * * * * * - - * *
#     * * * * * * - a * *
#     * * * - - T - - * *
#     * * - - * * t * * *
#     * * - * * * - - - *
#     * * - * * * * * c *
#     * - - - - - - - - *
#     v - * * * * * * * *
#     """

def turn_to_str_and_print(maze):
    maze_map = ''
    for i, row in enumerate(maze):
        new_row = ' '.join(row)
        if i < 9:
            maze_map += (new_row + '\n')
        else:
            maze_map += new_row
    print('Map:')
    print(maze_map)
    return maze_map

@click.command()
@click.option('--world_directory', type=str, help='The directory where to save worlds')
def generate_random_world(world_directory):

    # set random seed
    # np.random.seed(seed)

    print('Generating random world...')

    # Initialize maze with all obstacles
    maze = [['*' for j in range(10)] for i in range(10)]

    # Set bottom left and top right corners as roads
    maze[9][0] = '-'
    maze[9][1] = '-'
    maze[8][0] = '-'
    maze[8][1] = '-'
    maze[0][9] = '-'
    maze[0][8] = '-'
    maze[1][9] = '-'
    maze[1][8] = '-'

    weights = np.array([[20, 1, 1, 20], [20, 20, 1, 20], [20, 1, 20, 20]])
    # make rows sum to 1
    weights = weights / weights.sum(axis=1, keepdims=True)

    init_locs = [[8,1], np.random.randint(1, 8, size=2).tolist(), np.random.randint(1, 8, size=2).tolist()]
    for i in range(3):
        loc = init_locs[i]
        while loc != [1, 8]:
            # Choose one of the 4 directionas at random, with more probability of going right or up
            direction = np.random.choice(['right', 'down', 'left', 'up'], p=weights[i])

            # Move in that direction and make sure it's still in the maze
            if direction == 'right':
                loc[1] += 1
                if loc[1] >= 9:
                    loc[1] -= 1
            elif direction == 'down':
                loc[0] += 1
                if loc[0] >= 9:
                    loc[0] -= 1
            elif direction == 'left':
                loc[1] -= 1
                if loc[1] < 1:
                    loc[1] += 1
            elif direction == 'up':
                loc[0] -= 1
                if loc[0] < 1:
                    loc[0] += 1

            # Set that location as a road
            maze[loc[0]][loc[1]] = '-'

    # turn the maze into a string
    maze_map = turn_to_str_and_print(maze)

    # ask if the world is ok
    while True:
        answer = input('Is this world ok? (y/n)\n')
        if answer == 'y':
            break
        elif answer == 'n':
            process_completed = generate_random_world()
            if process_completed:
                return True
        else:
            print('Please type y or n')

    # ask for the location of the accident (a,b) or none
    while True:
        accident = input("Is there an accident? Give a pair of i,j coordinates or type 'n'\n")
        if accident == 'n':
            break
        else:
            try:
                accident = accident.split(',')
                accident = [int(i) for i in accident]
                maze[accident[0]][accident[1]] = 'a'
                break
            except:
                print("Please type a pair of valid i,j coordinates or type 'n'")
    maze_map = turn_to_str_and_print(maze)

    # ask for the location of the road closure (a,b) or none
    while True:
        road_closure = input("Is there a road closure? Give a pair of i,j coordinates or type 'n'\n")
        if road_closure == 'n':
            break
        else:
            try:
                road_closure = road_closure.split(',')
                road_closure = [int(i) for i in road_closure]
                maze[road_closure[0]][road_closure[1]] = 'c'
                break
            except:
                print("Please type a pair of valid i,j coordinates or type 'n'")
    maze_map = turn_to_str_and_print(maze)

    # ask for the number of traffic locations
    while True:
        traffic = input('How many traffic locations?\n')
        try:
            traffic = int(traffic)
            break
        except:
            print('Please type a valid number')

    # ask for the location of the traffic locations (a,b) and if they are active or not (t or T)
    for i in range(traffic):
        while True:
            traffic_loc = input(f'Give the location of traffic location {i+1} (i,j)\n')
            try:
                traffic_loc = traffic_loc.split(',')
                traffic_loc = [int(i) for i in traffic_loc]
                break
            except:
                print('Please type a pair of valid i,j coordinates')
        while True:
            active = input(f'Is traffic location {i+1} active? (y/n)\n')
            if active == 'y':
                maze[traffic_loc[0]][traffic_loc[1]] = 'T'
                break
            elif active == 'n':
                maze[traffic_loc[0]][traffic_loc[1]] = 't'
                break
            else:
                print('Please type y or n')
        maze_map = turn_to_str_and_print(maze)
    
    # set the initial agent location and the goal location
    maze[9][0] = 'v'
    maze[0][9] = 'g'

    print()
    print('The final world is:')
    maze_map = turn_to_str_and_print(maze)
    
    # ask for a name for the world
    while True:
        world_name = input('Give a name for the world\n')
        filename = ''.join([world_directory, world_name, '.txt'])
        if os.path.exists(filename):
            print('A world with that name already exists')
        else:
            break
    
    with open(filename, 'w') as f:
        f.write(maze_map)

    # if everything is ok, write the file and return True
    return True


if __name__ == '__main__':
    generate_random_world()