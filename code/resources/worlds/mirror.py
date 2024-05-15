# read world from txt file
world_file = 'world44.txt'

with open(world_file, 'r') as f:
    world_txt = f.read()
# print(world_txt)

# read lines, remove \n and spaces, and store in list of lists
world_list = []
for line in world_txt.split('\n'):
    world_list.append(line.split(' '))

# swap elements symmetric to the bottom left - top right diagonal
for i in range(len(world_list)):
    for j in range(len(world_list)-i):
        # swap elements
        world_list[i][j], world_list[len(world_list)-1-j][len(world_list)-1-i] = world_list[len(world_list)-1-j][len(world_list)-1-i], world_list[i][j]
        
# turn to txt again
world_txt = ''
for line in world_list:
    world_txt += ' '.join(line) + '\n'
# remove last \n
world_txt = world_txt[:-1]
# print(world_txt)

# write to file
with open(world_file, 'w') as f:
    f.write(world_txt)