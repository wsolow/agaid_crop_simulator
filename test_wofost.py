# Written Aug 2024, by Will Solow
# Test the WOFOST Gym environment
# With a few simple plots

import gymnasium as gym
import numpy as np
import wofost_gym
import matplotlib.pyplot as plt

from utils import NPK_Args
import tyro
import utils
from policies import default_policy as pol


if __name__ == "__main__":

    args = tyro.cli(NPK_Args)

    env_kwargs = {'args':args}
    env_id = args.env_id

    # Make the gym environment
    env = gym.make(env_id, **env_kwargs)
    env = utils.wrap_env_reward(env, args)

    obs_arr = []
    obs, info = env.reset(**{'year':2000})
    done = False
    obs_arr = []
    reward_arr = []

    while not done:
        action = pol(obs)
        next_obs, rewards, done, trunc, info = env.step(action)

        obs_arr.append(obs)
        reward_arr.append(rewards)

        # Append data
        obs = next_obs
        if done:
            obs, info = env.reset()
            break
    all_obs = np.array(obs_arr)

    plt.figure(0)
    plt.title('Rewards')
    plt.plot(np.cumsum(reward_arr))
    plt.show()
    
    all_vars = args.output_vars + args.weather_vars
    for i in range(len(all_vars)):
        plt.figure(i+1)
        plt.title(all_vars[i])
        plt.plot(all_obs[ :, i])  
        plt.show()



