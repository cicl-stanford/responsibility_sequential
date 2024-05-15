import matplotlib.pyplot as plt
import matplotlib
import numpy as np
import pickle
import click

def parse_initial_state(world_file, initial_agent):

    # read the maze map
    with open(world_file, 'r') as f:
        maze_map = f.read().split('\n')
    rows = []
    for row in maze_map:
        rows.append(row.split(' '))
    maze_map = np.array(rows, dtype='<U1')

    # get vehicle and goal locations directly from the map
    vehicle_loc = list(list(zip(*np.where(maze_map == 'v')))[0])
    goal_loc = list(list(zip(*np.where(maze_map == 'g')))[0])

    maze_map[vehicle_loc[0], vehicle_loc[1]] = '-'
    maze_map[goal_loc[0], goal_loc[1]] = '-'
    # get closure and accident locations from the map, if they exist
    closure_loc = list(zip(*np.where(maze_map == 'c')))
    if closure_loc == []:
        closure_loc = [-1, -1]
    else:
        closure_loc = list(closure_loc[0])
        maze_map[closure_loc[0], closure_loc[1]] = '-'

    accident_loc = list(zip(*np.where(maze_map == 'a')))
    if accident_loc == []:
        accident_loc = [-1, -1]
    else:
        accident_loc = list(accident_loc[0])
        maze_map[accident_loc[0], accident_loc[1]] = '-'
    
    # get traffic locations from the map, and set them to active if they are
    traffic_locs = []
    map_traffic_locs = list(zip(*np.where((maze_map == 't') | (maze_map == 'T'))))
    for traffic_loc in map_traffic_locs:
        if maze_map[traffic_loc[0], traffic_loc[1]] == 't':
            traffic_locs.append([traffic_loc[0], traffic_loc[1], 0])
            maze_map[traffic_loc[0], traffic_loc[1]] = '-'
        else:
            traffic_locs.append([traffic_loc[0], traffic_loc[1], 1])
            maze_map[traffic_loc[0], traffic_loc[1]] = '-'

    # initialize time_idle to 0 and get agent_name
    time_idle = 0

    return maze_map, vehicle_loc, goal_loc, closure_loc, accident_loc, traffic_locs, time_idle, initial_agent

def get_fig_dim(width, fraction=1, aspect_ratio=None):
    """Set figure dimensions to avoid scaling in LaTeX.

    Parameters
    ----------
    width: float
            Document textwidth or columnwidth in pts
    fraction: float, optional
            Fraction of the width which you wish the figure to occupy
    aspect_ratio: float, optional
            Aspect ratio of the figure

    Returns
    -------
    fig_dim: tuple
            Dimensions of figure in inches
    """
    # Width of figure (in pts)
    fig_width_pt = width * fraction

    # Convert from pt to inches
    inches_per_pt = 1 / 72.27

    if aspect_ratio is None:
        # If not specified, set the aspect ratio equal to the Golden ratio (https://en.wikipedia.org/wiki/Golden_ratio)
        aspect_ratio = (1 + 5**.5) / 2

    # Figure width in inches
    fig_width_in = fig_width_pt * inches_per_pt
    # Figure height in inches
    fig_height_in = fig_width_in / aspect_ratio

    fig_dim = (fig_width_in, fig_height_in)

    return fig_dim


def latexify(font_serif='Computer Modern', mathtext_font='cm', font_size=10, small_font_size=None, usetex=True):
    """Set up matplotlib's RC params for LaTeX plotting.
    Call this before plotting a figure.

    Parameters
    ----------
    font_serif: string, optional
		Set the desired font family
    mathtext_font: float, optional
    	Set the desired math font family
    font_size: int, optional
    	Set the large font size
    small_font_size: int, optional
    	Set the small font size
    usetex: boolean, optional
        Use tex for strings
    """

    if small_font_size is None:
        small_font_size = font_size

    params = {
        'backend': 'ps',
        'text.latex.preamble': '\\usepackage{gensymb} \\usepackage{bm}',
            
        'axes.labelsize': font_size,
        'axes.titlesize': font_size,
        'font.size': font_size,
        
        # Optionally set a smaller font size for legends and tick labels
        'legend.fontsize': small_font_size,
        'legend.title_fontsize': small_font_size,
        'xtick.labelsize': small_font_size,
        'ytick.labelsize': small_font_size,
        
        'text.usetex': usetex,    
        'font.family' : 'serif',
        'font.serif' : font_serif,
        'mathtext.fontset' : mathtext_font
    }

    matplotlib.rcParams.update(params)
    plt.rcParams.update(params)

@click.command()
@click.option('--factual_responses_file', required=True, help='File containing responses from the factual episode')
@click.option('--yn', required=True, help='counterfactual response is y or n')
@click.option('--cf_responses_file', required=True, help='File where counterfactual responses will be stored')
def cf_decision_responses(factual_responses_file, yn, cf_responses_file):
    
    # read the responses
    with open(factual_responses_file, 'rb') as f:
        responses = pickle.load(f)

    # find the first 'y' in the list of responses
    for i, response in enumerate(responses):
        if response == 'y':
            loc_prompt = i
            break
    cf_responses = responses[:loc_prompt+1]
    cf_responses.append(yn+'cf')
    cf_responses.append(responses[-1])

    # write the responses
    with open(cf_responses_file, 'wb') as f:
        pickle.dump(cf_responses, f)

if __name__ == '__main__':
    cf_decision_responses()