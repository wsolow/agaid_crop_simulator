import gymnasium as gym
import numpy as np
import wofost_gym
import matplotlib.pyplot as plt

from utils import NPK_Args
import tyro



def policy(obs):
    action = [0,0,0,0]
    if obs[7] < 1.0:
        action[0] = 1
    if obs[8] < 1.0:
        action[1] = 1
    if obs[9] < 1.0:
        action[2] = 1
    if obs[10] < 25.0:
        action[3] = 2

    return action

if __name__ == "__main__":

    args = tyro.cli(NPK_Args)

    env_kwargs = {'args':args}
    env_id = 'npk-v0'

    # Make the gym environment
    env = gym.make(env_id, **env_kwargs)

    obs_arr = []
    obs, info = env.reset()
    done = False
    curr_reward = 0
    obs_arr = []

    while not done:
        action = policy(obs)
        next_obs, rewards, done, trunc, info = env.step(action)
        curr_reward += rewards
        obs_arr.append(obs)
        # Append data
        obs = next_obs
        if done:
            obs, info = env.reset()
            break
    all_obs = np.array(obs_arr)

    for i in range(len(args.output_vars)):
        plt.figure(i)
        plt.title(args.output_vars[i])
        plt.plot(all_obs[ :, i])  
        plt.show()



