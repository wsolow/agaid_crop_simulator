from dataclasses import dataclass, field
from pathlib import Path
import wofost_gym.wrappers.wrappers as wrappers
import typing
import gymnasium as gym


# Configuration parameters for NPK WOFOST Gym Environment
@dataclass
class NPK_Args:
    """Environment ID"""
    env_id: str = "wofost-v0"
    """Env Reward Function"""
    env_reward: str = "default"
    """Environment seed"""
    seed: int = 0
    """Path"""
    path: str = "/Users/wsolow/Projects/agaid_crop_simulator/"

    """Output Variables"""
    """See env_config/README.md for more information"""
    output_vars: list = field(default_factory = lambda: ['DVS', 'LAI', 'RD', 'WSO', 'NAVAIL', 'PAVAIL', 'KAVAIL', 'WC', 'SM'])
    """Weather Variables"""
    weather_vars: list = field(default_factory = lambda: ['IRRAD', 'TMIN', 'TMAX', 'TEMP', 'VAP', 'RAIN', 'WIND'])

    """Intervention Interval"""
    intvn_interval: int = 1
    """Number of NPK Fertilization Actions"""
    """Total number of actions available will be 3*num_fert^3 + num_irrig"""
    num_fert: int = 2
    """Number of Irrgiation Actions"""
    num_irrig: int = 2

    """Coefficient for Nitrogen Recovery after fertilization"""
    n_recovery: float = 0.7
    """Coefficient for Phosphorous Recovery after fertilization"""
    p_recovery: float = 0.7
    """Coefficient for Potassium Recovery after fertilization"""
    k_recovery: float = 0.7
    """Amount of fertilizer coefficient in kg/ha"""
    fert_amount: float = 2
    """Amount of water coefficient in cm/water"""
    irrig_amount: float  = 0.5
    """Coefficient for cost of fertilization"""
    beta: float = 10.0

    """Relative path to agromanagement configuration file"""
    agro_fpath: str = "env_config/agro_config/test_agro_npk.yaml"
    """Relative path to crop configuration file"""
    crop_fpath: str = "env_config/crop_config/"
    """Relative path to site configuration file"""
    site_fpath: str = "env_config/site_config/"

    """Flag for resetting to random year"""
    random_reset: bool = False

# Function to wrap the environment with a given reward function
# Based on the reward functions created in the wofost_gym/wrappers/
def wrap_env_reward(env: gym.Env, args: NPK_Args):
    if args.env_reward == "default":
        return env
    elif args.env_reward == "totalgrowth":
        return wrappers.RewardTotalGrowthWrapper(env)
    elif args.env_reward == "fertilizationcost":
        return wrappers.RewardFertilizationCostWrapper