# Written 2024, by Will Solow
# A file contanining many different fertilization and irrigation policies
# 

# Default policy, which performs no irrigation or fertilization action
# at any point in the simulation
def default_policy(obs):
    return [0,0]

def n_weekly(obs):
    if obs[-1] % 7 == 0:
        return [0,1]
    return [0,0]