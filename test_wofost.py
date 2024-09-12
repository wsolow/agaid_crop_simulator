# Written Aug 2024, by Will Solow
# Test the WOFOST Gym environment
# With a few simple plots

import gymnasium as gym
import numpy as np
import sys
import wofost_gym
import matplotlib.pyplot as plt

from wofost_gym.args import NPK_Args
import tyro
import utils
import policies

def norm(x):
    return (x-np.nanmin(x))/(np.nanmax(x)-np.nanmin(x))


if __name__ == "__main__":

    args = tyro.cli(NPK_Args)

    env_kwargs = {'args':args}
    env_id = args.env_id

    # Make the gym environment
    env = gym.make(env_id, **env_kwargs)
    
    
    env = wofost_gym.wrappers.RewardFertilizationThresholdWrapper(env, max_n=50)
    env = wofost_gym.wrappers.NPKDictActionWrapper(env)
    env = wofost_gym.wrappers.NPKDictObservationWrapper(env)
    
    
    #print(env.action_space.sample)
    #env = utils.wrap_env_reward(env, args)

    obs_arr = []
    obs, info = env.reset()
    done = False
    obs_arr = []
    reward_arr = []
    k = 0
    policy = policies.Weekly_N(env,amount=2)

    action = {'plant':0, 'harvest':0, 'n':0, 'p':0, 'k':0, 'irrig':0}
    while not done:
        action = policy(obs)
        next_obs, rewards, done, trunc, info = env.step(action)
        obs_arr.append(obs)
        reward_arr.append(rewards)

        # Append data
        obs = next_obs
        k += 1
        if done:
            obs, info = env.reset()
            break
    all_obs = np.array(obs_arr)

    plt.figure(0)
    plt.title('Rewards')
    plt.plot(np.cumsum(reward_arr))
    plt.show()
    
    all_vars = args.output_vars + args.forecast_length * args.weather_vars
    k=0
    plt.figure()
    for i in range(len(all_vars)):
        alpha=.5
        if all_vars[i] == 'TEMP':
            
            plt.title(all_vars[i])
            if k == 0:
                alpha=1
            plt.plot(all_obs[ :, i], alpha=alpha, label=f'Day: {k}')
            k+=1
    plt.legend()
    k = 0
    plt.figure()
    for i in range(len(all_vars)):
        alpha=.5
        if all_vars[i] == 'IRRAD':
            
            plt.title(all_vars[i])
            if k == 0:
                alpha=1
            plt.plot(all_obs[ :, i], alpha=alpha, label=f'Day: {k}')
            k+=1
    plt.legend()
    plt.show()
    for i in range(len(all_vars)):
        plt.figure(i+1)
        plt.title(all_vars[i])
        plt.plot(all_obs[ :, i])
        plt.plot(all_obs[ :, 0])
        plt.xlim(0-10, all_obs.shape[0]+10) 
    plt.show()

    sys.exit(0)
    for i in range(len(all_vars)):
        plt.plot(norm(all_obs[ :, i]), label=all_vars[i])
        plt.xlim(0-10, all_obs.shape[0]+10) 

    plt.legend()
    plt.show()





