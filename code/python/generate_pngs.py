import matplotlib.pyplot as plt
import json
from PIL import Image
import numpy as np
from matplotlib.patches import Rectangle, Circle
import click
import os
import shutil

def is_in_FOV(point_x, point_y, vehicle_x, vehicle_y):
    if (vehicle_x-1 <= point_x <= vehicle_x+1) and (vehicle_y-1 <= point_y <= vehicle_y+1):
        return True
    else:
        return False

def get_FOV(vehicle_x, vehicle_y, x_dim, y_dim):
    bottom_left = [max(0, vehicle_x-1), max(0, vehicle_y-1)]
    top_right = [min(x_dim-1, vehicle_x+1), min(y_dim-1, vehicle_y+1)]
    return [bottom_left, top_right]

# Define a function to update the plot for each frame
def timestep_png(t, maze_map, accident_loc, closure_loc, goal_loc, traffic_locs, episode_data, images, episode_png_directory, episode_length, durations, time_goal, no_car=False, summary=False, dialog=None):

    # Create a new figure and axis
    
    aspect=len(maze_map)/len(maze_map[0])
    fig, ax = plt.subplots(figsize=(3, 3*aspect), dpi=300)

    step_data = episode_data[t]
    action = step_data['action']
    codriver_action = step_data['codriver_action']
    if no_car:
        agent_name = 'human'
    else:
        agent_name = step_data['agent_name']
    tiles_explored = step_data['tiles_explored']
    vehicle_loc = step_data['vehicle_loc']

    # Clear the axis and redraw the maze
    ax.clear()
    for i in range(len(maze_map)):
        for j in range(len(maze_map[0])):
            if tiles_explored[i][j] == 0:
                alpha = 0.4
            else:
                alpha = 1.0

            if maze_map[i][j] == 1:
                # wall
                alpha = 1.0
                ax.fill([j, j+1, j+1, j], [len(maze_map)-i-1, len(maze_map)-i-1, len(maze_map)-i, len(maze_map)-i], 'black', alpha=alpha, zorder=0)
            elif maze_map[i][j] == 0 and [i, j] == goal_loc:
                # goal
                ax.fill_between([j, j+1], len(maze_map)-i, len(maze_map)-i-1, facecolor='none', edgecolor='black', linewidth=1, alpha=1.0, zorder=0)
                alpha = 1.0
                ax.imshow(images['goal'], extent=[j, j+1, len(maze_map)-i-1, len(maze_map)-i], alpha=alpha, zorder=0)
            elif maze_map[i][j] == 0 and [i, j] == closure_loc:
                # road closure
                ax.fill_between([j, j+1], len(maze_map)-i, len(maze_map)-i-1, facecolor='none', edgecolor='black', linewidth=1, alpha=1.0, zorder=0)
                if agent_name == 'human':
                    alpha = 1.0
                ax.imshow(images['closure'], extent=[j, j+1, len(maze_map)-i-1, len(maze_map)-i], alpha=alpha, zorder=0)
            elif maze_map[i][j] == 0 and [i, j] == accident_loc:
                # accident
                ax.fill_between([j, j+1], len(maze_map)-i, len(maze_map)-i-1, facecolor='none', edgecolor='black', linewidth=1, alpha=1.0, zorder=0)
                if tiles_explored[i][j] != 0:
                    ax.imshow(images['accident'], extent=[j, j+1, len(maze_map)-i-1, len(maze_map)-i], zorder=0)
            else:
                # traffic or normal road
                if agent_name == 'ai' or tiles_explored[i][j] == 1:
                    alpha = 1.0
                else:
                    alpha = 0.4
                traffic_loc = [[x[0], x[1], x[2]] for x in traffic_locs if x[0] == i and x[1] == j]
                if traffic_loc != [] and traffic_loc[0][2]==1:
                    ax.fill_between([j, j+1], len(maze_map)-i, len(maze_map)-i-1, facecolor='none', edgecolor='black', linewidth=1, alpha=1.0, zorder=0)
                    w=0.02
                    ax.fill([j+w, j+1-w, j+1-w, j+w], [len(maze_map)-i-1+w, len(maze_map)-i-1+w, len(maze_map)-i-w, len(maze_map)-i-w], '#ff3a3a', alpha=alpha, zorder=0)
                elif traffic_loc != [] and traffic_loc[0][2]==0:

                    ax.fill_between([j, j+1], len(maze_map)-i, len(maze_map)-i-1, facecolor='none', edgecolor='black', linewidth=1, alpha=1.0, zorder=0)
                    w=0.02
                    ax.fill([j+w, j+1-w, j+1-w, j+w], [len(maze_map)-i-1+w, len(maze_map)-i-1+w, len(maze_map)-i-w, len(maze_map)-i-w], '#ff3a3a', alpha=alpha, zorder=0)
                    ww = 5*w
                    ax.fill([j+ww, j+1-ww, j+1-ww, j+ww], [len(maze_map)-i-1+ww, len(maze_map)-i-1+ww, len(maze_map)-i-ww, len(maze_map)-i-ww], 'white', alpha=1.0, zorder=0)
                elif traffic_loc == []:
                    ax.fill_between([j, j+1], len(maze_map)-i, len(maze_map)-i-1, facecolor='none', edgecolor='black', linewidth=1, alpha=1.0, zorder=0)

    # Draw the vehicle
    if agent_name == 'human':
        # color = "#f5a997"
        color = "#ba45ab"
    elif agent_name == 'ai':
        color = "#ffa000"

    vehicle_xy_loc = [vehicle_loc[1], len(maze_map)-vehicle_loc[0]-1]
    bottom_left, top_right = get_FOV(vehicle_xy_loc[0], vehicle_xy_loc[1], len(maze_map[0]), len(maze_map))
    if (not no_car) and (not summary):
        # Draw the field of vision only if not in summary or intro mode
        ax.add_patch(Rectangle(xy=bottom_left, width = top_right[0]-bottom_left[0]+1, height = top_right[1]-bottom_left[1]+1, color = color, fill=False, linewidth=2, zorder=2))

    reached = False
    extent=[vehicle_loc[1], vehicle_loc[1]+1, len(maze_map)-vehicle_loc[0]-1, len(maze_map)-vehicle_loc[0]]
    if no_car:
        # if agent_name == 'human':
        #     ax.imshow(images['human'], extent=extent, zorder=2)
        # elif agent_name == 'ai':
        #     ax.imshow(images['aiRight'], extent=extent, zorder=2)
        ax.imshow(images['human'], extent=extent, zorder=2)
    else:
        if agent_name == 'human':
            if vehicle_loc == goal_loc:
                ax.imshow(images['humanCheck'], extent=extent, zorder=2)
                reached = True
            else:
                if t == time_goal:
                    ax.imshow(images['humanX'], extent=extent, zorder=2)
                else:
                    if action == 'u' or action == 'uc':
                        ax.imshow(images['humanUp'], extent=extent, zorder=2)
                    elif action == 'd' or action == 'dc':
                        ax.imshow(images['humanDown'], extent=extent, zorder=2)
                    elif action == 'l' or action == 'lc':
                        ax.imshow(images['humanLeft'], extent=extent, zorder=2)
                    elif action == 'r' or action == 'rc':
                        ax.imshow(images['humanRight'], extent=extent, zorder=2)
        elif agent_name == 'ai':
            if vehicle_loc == goal_loc:
                ax.imshow(images['aiCheck'], extent=extent, zorder=2)
                reached = True
            else:
                if t == time_goal:
                    ax.imshow(images['aiX'], extent=extent, zorder=2)
                else:
                    if action == 'u' or action =='uc':
                        ax.imshow(images['aiUp'], extent=extent, zorder=2)
                    elif action == 'd' or action == 'dc':
                        ax.imshow(images['aiDown'], extent=extent, zorder=2)
                    elif action == 'l' or action == 'lc':
                        ax.imshow(images['aiLeft'], extent=extent, zorder=2)
                    elif action == 'r' or action == 'rc':
                        ax.imshow(images['aiRight'], extent=extent, zorder=2)
    
    # Show the human-AI dialog
    if summary and (dialog is not None):
        # In summary mode, the dialog is shown at the given location
        dialog_loc = dialog[0]
        dialog_text = dialog[1]

        props = dict(boxstyle='round', facecolor='#FFEED2', alpha=1.0)
        if dialog_loc == vehicle_xy_loc:
            # Special case when the position of the dialog box is the same as the final vehicle location
            if agent_name == 'human':
                if vehicle_xy_loc[0]+1>=len(maze_map[0])/2:
                    loc_x, loc_y = vehicle_xy_loc[0]-1.3, vehicle_xy_loc[1]+1.6
                else:
                    loc_x, loc_y = vehicle_xy_loc[0]+1, vehicle_xy_loc[1]+1.6
            elif agent_name == 'ai':
                if vehicle_xy_loc[0]+1>=len(maze_map[0])/2:
                    loc_x, loc_y = vehicle_xy_loc[0]-0.9, vehicle_xy_loc[1]+1.6
                else:
                    loc_x, loc_y = vehicle_xy_loc[0]+1, vehicle_xy_loc[1]+1.6
        else:
            # Place the dialog box exactly where it appeared in the episode
            loc_x, loc_y = dialog_loc[0]+0.1, dialog_loc[1]+0.9

        loc_x = max(1, loc_x)
        loc_y = min(len(maze_map)-0.2, loc_y)
        ax.text(loc_x, loc_y, dialog_text, fontsize=7, verticalalignment='top', bbox=props)
        
        timestep_dialog_loc = None
        timestep_dialog_text = None

    elif t < episode_length-1 and (action in {'uc', 'dc', 'lc', 'rc'}):
        # In normal mode, the dialog is shown next to the vehicle location
        if agent_name == 'ai':
        
            if action == 'uc':
                # ai_text = 'Going up, please confirm.'
                ai_text = u'▲?'
                # ai_text = 'Override?'
            elif action == 'dc':
                # ai_text = 'Going down, please confirm.'
                ai_text = u'▼?'
                # ai_text = 'Override?'
            elif action == 'lc':
                # ai_text = 'Going left, please confirm.'
                ai_text = u'◀?'
                # ai_text = 'Override?'
            elif action == 'rc':
                # ai_text = 'Going right, please confirm.'
                ai_text = u'▶?'
                # ai_text = 'Override?'
            if agent_name != episode_data[t+1]['agent_name']:
                # human_text = 'I want to take over.'
                human_text = u'✖'
            else:
                # human_text = 'Keep going.'
                human_text = u'✔'

        elif agent_name == 'human':
            
            if codriver_action in {'u', 'uc'}:
                # ai_text = 'Shall I take over?'
                ai_text = 'Help?'
            elif codriver_action in {'d', 'dc'}:
                ai_text = 'Help?'
            elif codriver_action in {'l', 'lc'}:
                ai_text = 'Help?'
            elif codriver_action in {'r', 'rc'}:
                ai_text = 'Help?'
        
            if agent_name != episode_data[t+1]['agent_name']:
                human_text = u'✔'
            else:
                human_text = u'✖'
        
        props = dict(boxstyle='round', facecolor='#FFEED2', alpha=1.0)
        if agent_name == 'human':
            if vehicle_xy_loc[0]+1>=len(maze_map[0])/2:
                loc_x, loc_y = vehicle_xy_loc[0]-1.3, vehicle_xy_loc[1]+1.6
            else:
                loc_x, loc_y = vehicle_xy_loc[0]+1, vehicle_xy_loc[1]+1.6
        elif agent_name == 'ai':
            if vehicle_xy_loc[0]+1>=len(maze_map[0])/2:
                loc_x, loc_y = vehicle_xy_loc[0]-0.9, vehicle_xy_loc[1]+1.6
            else:
                loc_x, loc_y = vehicle_xy_loc[0]+1, vehicle_xy_loc[1]+1.6
        
        # Store the location and text of the dialog box
        timestep_dialog_loc = [vehicle_xy_loc[0], vehicle_xy_loc[1]]
        timestep_dialog_text = 'AI: ' + ai_text + '\nJ:   ' + human_text

        loc_x = max(1, loc_x)
        loc_y = min(len(maze_map)-0.2, loc_y)
        ax.text(loc_x, loc_y, 'AI: ' + ai_text + '\nJ:   ' + human_text, fontsize=7, verticalalignment='top', bbox=props)
        
        # human-AI dialog -> set the frame duration to 2 seconds
        if not no_car and not summary:
            durations.append(2000)
    else:
        # Set these values to None to avoid errors
        timestep_dialog_loc = None
        timestep_dialog_text = None
        # no interaction -> set the frame duration to half a second
        if not no_car and not summary:
            durations.append(500)
    
    # Draw the vehicle path
    line_width = 2
    for i in range(0, t+1):
        position = episode_data[i]['vehicle_loc']
        agent_name = episode_data[i]['agent_name']
        
        
        if i == 0:
            # draw a circle at the vehicle position
            if agent_name == 'human':
                color = "#762c6c"
            elif agent_name == 'ai':
                color = "#ffa000"
            ax.add_patch(Circle(xy=[position[1]+0.5, len(maze_map)-position[0]-0.5], radius=0.15, edgecolor=None, facecolor=color, fill=True, zorder=1, alpha=0.5))
            previous_position = position
        else:
            # draw a line between the previous position and the current position
            ax.plot([previous_position[1]+0.5, position[1]+0.5], [len(maze_map)-previous_position[0]-0.5, len(maze_map)-position[0]-0.5], color=color,\
                        linewidth=line_width, linestyle='dashed', marker=None, zorder=1, alpha=0.5)
            if agent_name == 'human':
                color = "#762c6c"
            elif agent_name == 'ai':
                color = "#ffa000"
            # draw a circle at the vehicle position
            ax.add_patch(Circle(xy=[position[1]+0.5, len(maze_map)-position[0]-0.5], radius=0.15, edgecolor=None, facecolor=color, fill=True, zorder=1, alpha=0.5))
            previous_position = position


    # Set the axis limits and save the figure
    ax.set_ylim(0, len(maze_map))
    ax.set_xlim(0, len(maze_map[0]))
    ax.axis('off')
    ax.set_title('Time remaining: {rem}'.format(rem=time_goal-t), fontsize=6)
    fig.tight_layout()
    if no_car:
        fig.savefig(''.join([episode_png_directory, f'intro.png']), dpi=300)
    elif summary:
        fig.savefig(''.join([episode_png_directory, f'summary.png']), dpi=300)
    else:
        fig.savefig(''.join([episode_png_directory, f'frame_{t}.png']), dpi=300)
    plt.close()

    return reached, timestep_dialog_loc, timestep_dialog_text

@click.command()
@click.option('--log_file', type=str, help='Directory where episode simulation data are stored')
@click.option('--png_directory', type=str, help='Directory where the generated PNG files are stored')
@click.option('--icon_directory', type=str, help='Directory where the icons are stored')
@click.option('--loop_gif', is_flag=True, help='Whether to loop the GIF file')
def generate_pngs(log_file, png_directory, icon_directory, loop_gif):

    # read logs from JSON file
    with open(log_file, 'r') as f:
        logs = json.load(f)

    maze_map = logs['maze_map']
    accident_loc = logs['accident_loc']
    closure_loc = logs['closure_loc']
    goal_loc = logs['goal_loc']
    traffic_locs = logs['traffic_locs']
    episode_length = logs['length']
    episode_data = logs['time_steps']

    # ask the user to input the time goal
    time_goal = int(input('Please enter the time goal: '))
    # make sure it is a positive integer
    while time_goal <= 0:
        time_goal = int(input('Please enter a positive integer: '))

    # load the images from separate PNG files
    image_files = ['human.png', 'goal.png', 'closure.png', 'accident.png', 'humanUp.png', 'humanDown.png', 'humanLeft.png', 'humanRight.png',\
                        'aiUp.png', 'aiDown.png', 'aiLeft.png', 'aiRight.png', 'humanCheck.png', 'aiCheck.png', 'humanX.png', 'aiX.png']
    images = {}
    for filename in image_files:
        img = Image.open(icon_directory + filename).convert('RGBA')
        arr = np.array(img)
        images[filename.split('.')[0]] = arr

    def remove_suffix(input_string, suffix):
        if suffix and input_string.endswith(suffix):
            return input_string[:-len(suffix)]
        return input_string

    # read log file parameters and name png directory
    params = remove_suffix(log_file.split('/')[-1], '.json').split('_')
    params = {p.split(':')[0] : p.split(':')[1] for p in params}
    init_agent = params['initagent']
    world_name = params['manuallogs']
    explanation = params['explanation']
    episode_png_directory = ''.join([png_directory, world_name, '_', init_agent, '_', explanation, '/'])
    
    # check if the directory exists
    if os.path.exists(episode_png_directory) and os.path.isdir(episode_png_directory):
        # remove all files and subdirectories in the directory
        for filename in os.listdir(episode_png_directory):
            file_path = os.path.join(episode_png_directory, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print(f"Failed to delete {file_path}. Reason: {e}")
    else:
        # create the directory
        os.makedirs(episode_png_directory)

    durations = []
    # Draw the intro frame
    _ = timestep_png(0, maze_map, accident_loc, closure_loc, goal_loc, traffic_locs, episode_data, images, episode_png_directory, episode_length, durations, time_goal, no_car=True)
    num_of_frames = 0
    dialog_loc = None
    dialog_text = None
    for t in range(0, time_goal+1):
        # Draw the timestep frame
        reached, timestep_dialog_loc, timestep_dialog_text = timestep_png(t, maze_map, accident_loc, closure_loc, goal_loc, traffic_locs, episode_data, images, episode_png_directory, episode_length, durations, time_goal)
        if timestep_dialog_loc is not None:
            dialog_loc = timestep_dialog_loc
            dialog_text = timestep_dialog_text
        num_of_frames += 1
        if reached:
            break
    dialog = (dialog_loc, dialog_text) if dialog_loc is not None else None
    # Draw the summary frame
    _ = timestep_png(t, maze_map, accident_loc, closure_loc, goal_loc, traffic_locs, episode_data, images, episode_png_directory, episode_length, durations, time_goal, summary=True, dialog=dialog)

    # combine all the generated pngs into a single GIF file
    # png_files = [''.join([episode_png_directory, filename]) for filename in sorted(os.listdir(episode_png_directory), key=lambda x: int(x.split('_')[1].split('.')[0])) if filename != 'intro.png']
    png_files = [''.join([episode_png_directory, 'frame_', str(t), '.png']) for t in range(0, num_of_frames)]
    # Create a list of images from the PNGs
    images = [Image.open(png_file) for png_file in png_files]

    # Save the images as a GIF
    frame_one = images[0]
    if loop_gif:
        durations[-1] = 2000
        frame_one.save(''.join([episode_png_directory, 'episode.gif']), format="GIF", append_images=images[1:],
               save_all=True, duration=durations, loop=0)
    else:
        frame_one.save(''.join([episode_png_directory, 'episode.gif']), format="GIF", append_images=images[1:],
                save_all=True, duration=durations)

if __name__ == '__main__':
    generate_pngs()