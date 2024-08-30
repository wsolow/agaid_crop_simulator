import gymnasium as gym
import numpy as np
import wofost_gym
import matplotlib.pyplot as plt

from utils import NPK_Args
import tyro
import utils



def policy(obs, k):
    if k % 4 == 0:
        action = [3,0]
    elif k % 4 == 1:
        action = [2, 3]
    else:
        action = [0,1]

    return action

if __name__ == "__main__":

    args = tyro.cli(NPK_Args)

    env_kwargs = {'args':args}
    env_id = args.env_id

    # Make the gym environment
    env = gym.make(env_id, **env_kwargs)
    env = utils.wrap_env_reward(env, args)

    obs_arr = []
    obs, info = env.reset()
    done = False
    curr_reward = 0
    obs_arr = []
    reward_arr = []

    k=0
    while not done:
        k+=1 
        action = policy(obs, k)
        next_obs, rewards, done, trunc, info = env.step(action)
        curr_reward += rewards
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

    for i in range(len(args.output_vars)):
        plt.figure(i+1)
        plt.title(args.output_vars[i])
        plt.plot(all_obs[ :, i])  
        plt.show()



