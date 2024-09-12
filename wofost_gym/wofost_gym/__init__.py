"""Entry point for WOFOST_Gym package. Handles imports and Gym Environment
registration.
"""

from gymnasium.envs.registration import register
from wofost_gym import args
from wofost_gym import utils
from wofost_gym import exceptions

# Default single year environments
register(
    id='lnpkw-v0',
    entry_point='wofost_gym.envs.wofost_default_singleyear:Limited_NPKW_Env',
)
register(
    id='pp-v0',
    entry_point='wofost_gym.envs.wofost_default_singleyear:PP_Env',
)
register(
    id='lnpk-v0',
    entry_point='wofost_gym.envs.wofost_default_singleyear:Limited_NPK_Env',
)
register(
    id='ln-v0',
    entry_point='wofost_gym.envs.wofost_default_singleyear:Limited_N_Env',
)
register(
    id='lnw-v0',
    entry_point='wofost_gym.envs.wofost_default_singleyear:Limited_NW_Env',
)
register(
    id='lw-v0',
    entry_point='wofost_gym.envs.wofost_default_singleyear:Limited_W_Env',
)

# Single year Harvest Environments
register(
    id='harvest-npk-v0',
    entry_point='wofost_gym.envs.wofost_harvest_singleyear:Harvest_LNPKW_Env',
)
register(
    id='harvest-pp-v0',
    entry_point='wofost_gym.envs.wofost_harvest_singleyear:Harvest_PP_Env',
)
register(
    id='harvest-lnpk-v0',
    entry_point='wofost_gym.envs.wofost_harvest_singleyear:Harvest_Limited_NPK_Env',
)
register(
    id='harvest-ln-v0',
    entry_point='wofost_gym.envs.wofost_harvest_singleyear:Harvest_Limited_N_Env',
)
register(
    id='harvest-lnw-v0',
    entry_point='wofost_gym.envs.wofost_harvest_singleyear:Harvest_Limited_NW_Env',
)
register(
    id='harvest-lw-v0',
    entry_point='wofost_gym.envs.wofost_harvest_singleyear:Harvest_Limited_W_Env',
)

