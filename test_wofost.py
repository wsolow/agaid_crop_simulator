"""File for testing the installation and setup of the WOFOST Gym Environment
with a few simple plots for output 

Written by: Will Solow, 2024
"""

import gymnasium as gym
import numpy as np
import tyro
import matplotlib.pyplot as plt

import wofost_gym
import wofost_gym.policies as policies
from utils import Args
import utils


if __name__ == "__main__":

    args = tyro.cli(Args)

    env_id, env_kwargs = utils.get_gym_args(args)

    # Make the gym environment with wrappers
    env = gym.make(env_id, **env_kwargs)
    env = wofost_gym.wrappers.RewardFertilizationThresholdWrapper(env, max_n=50)
    env = wofost_gym.wrappers.NPKDictActionWrapper(env)
    env = wofost_gym.wrappers.NPKDictObservationWrapper(env)
    
    # Set default policy for use
    policy = policies.No_Action(env)

    obs_arr = []
    obs, info = env.reset()
    done = False
    obs_arr = []
    reward_arr = []

    # Run simulation and store data
    k = 0
    while not done:
        action = policy(obs)
        next_obs, rewards, done, trunc, info = env.step(action)
        obs_arr.append(obs)
        reward_arr.append(rewards)
        obs = next_obs
        k+=1
        print(k)
        if done:
            obs, info = env.reset()
            break
    all_obs = np.array([list(d.values()) for d in obs_arr])

    all_vars = args.npk_args.output_vars + args.npk_args.forecast_length * args.npk_args.weather_vars

    # Plot Data
    plt.figure(0)
    plt.title('Cumulative Rewards')
    plt.xlabel('Days')
    plt.plot(np.cumsum(reward_arr))
    
    plt.figure()
    for i in range(len(all_vars)):
        plt.figure(i+1)
        plt.title(all_vars[i])
        plt.plot(all_obs[ :, i])
        plt.xlim(0-10, all_obs.shape[0]+10) 
        plt.xlabel('Days')
    plt.show()






