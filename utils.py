"""File for utils functions. Importantly contains:
    - Args: Dataclass for configuring paths for the WOFOST Environment
    - get_gym_args: function for getting the required arguments for the gym 
    environment from the Args dataclass 

Written by: Will Solow, 2024
"""



import gymnasium as gym
import warnings
import numpy as np 
from dataclasses import dataclass, field

import wofost_gym.wrappers.wrappers as wrappers
from wofost_gym.args import NPK_Args

warnings.filterwarnings("ignore", category=UserWarning)

@dataclass
class Args:
    """Dataclass for configuration a Gym environment
    """

    """Parameters for the NPK Gym Environment"""
    npk_args: NPK_Args

    """Environment ID"""
    env_id: str = "lnpkw-v0"
    """Env Reward Function"""
    env_reward: str = "default"

    """Location of data folder which contains multiple runs"""
    save_folder: str = "data/"

    """Path"""
    base_fpath: str = "/Users/wsolow/Projects/agaid_crop_simulator/"
    """Relative path to agromanagement configuration file"""
    agro_fpath: str = "env_config/agro_config/annual_agro_npk.yaml"
    """Relative path to crop configuration file"""
    crop_fpath: str = "env_config/crop_config/"
    """Relative path to site configuration file"""
    site_fpath: str = "env_config/site_config/"

    """Path to policy if using a trained Deep RL Agent Policy"""
    """Typically in wandb/files/"""
    agent_path: str = None
    """Agent type (PPO, DQN, SAC)"""
    agent_type: str = None
    """Policy name if using a policy in the policies.py file"""
    policy_name: str = None

    """Year range, incremented by 1"""
    year_range: list = field(default_factory = lambda: [1984, 2000])
    """Latitude Range, incremented by .5"""
    lat_range: list = field(default_factory = lambda: [50, 50])
    """Longitude Range of values, incremented by .5"""
    long_range: list = field(default_factory = lambda: [5, 5])

def get_gym_args(args: Args):
    """Returns the Environment ID and required arguments for the WOFOST Gym
    Environment

    Arguments:
        Args: Args dataclass
    """
    env_kwargs = {'args': args.npk_args, 'base_fpath': args.base_fpath, \
                  'agro_fpath': args.agro_fpath,'site_fpath': args.site_fpath, 
                  'crop_fpath': args.crop_fpath }
    
    return args.env_id, env_kwargs


def norm(x):
    return (x-np.nanmin(x))/(np.nanmax(x)-np.nanmin(x))


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