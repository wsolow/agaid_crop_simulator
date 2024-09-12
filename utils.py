
from pathlib import Path
import wofost_gym.wrappers.wrappers as wrappers
import typing
import gymnasium as gym
import warnings
from inspect import getmembers, isfunction
import datetime

warnings.filterwarnings("ignore", category=UserWarning)


# Function to wrap the environment with a given reward function
# Based on the reward functions created in the wofost_gym/wrappers/
def wrap_env_reward(env: gym.Env, args):


    if args.env_reward == "default":
        print('Default Reward Function')
        return env
    elif args.env_reward == "fertilizationcost":
        print('Fertilization Cost Reward Function')
        return wrappers.RewardFertilizationCostWrapper(env)
    elif args.env_reward == 'fertilization_threshold':
        print('Fertilization Threshold Reward Function')
        return wrappers.RewardFertilizationThresholdWrapper(env)