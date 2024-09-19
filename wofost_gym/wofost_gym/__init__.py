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
    entry_point='wofost_gym.envs.wofost_annual:Limited_NPKW_Env',
)
register(
    id='pp-v0',
    entry_point='wofost_gym.envs.wofost_annual:PP_Env',
)
register(
    id='lnpk-v0',
    entry_point='wofost_gym.envs.wofost_annual:Limited_NPK_Env',
)
register(
    id='ln-v0',
    entry_point='wofost_gym.envs.wofost_annual:Limited_N_Env',
)
register(
    id='lnw-v0',
    entry_point='wofost_gym.envs.wofost_annual:Limited_NW_Env',
)
register(
    id='lw-v0',
    entry_point='wofost_gym.envs.wofost_annual:Limited_W_Env',
)

# Single year Harvest Environments
register(
    id='harvest-npk-v0',
    entry_point='wofost_gym.envs.plant_annual:Harvest_LNPKW_Env',
)
register(
    id='harvest-pp-v0',
    entry_point='wofost_gym.envs.plant_annual:Harvest_PP_Env',
)
register(
    id='harvest-lnpk-v0',
    entry_point='wofost_gym.envs.plant_annual:Harvest_Limited_NPK_Env',
)
register(
    id='harvest-ln-v0',
    entry_point='wofost_gym.envs.plant_annual:Harvest_Limited_N_Env',
)
register(
    id='harvest-lnw-v0',
    entry_point='wofost_gym.envs.plant_annual:Harvest_Limited_NW_Env',
)
register(
    id='harvest-lw-v0',
    entry_point='wofost_gym.envs.plant_annual:Harvest_Limited_W_Env',
)

# Default perennial environments
register(
    id='perennial-lnpkw-v0',
    entry_point='wofost_gym.envs.wofost_perennail:Perennial_Limited_NPKW_Env',
)
register(
    id='perennial-pp-v0',
    entry_point='wofost_gym.envs.wofost_perennail:Perennial_PP_Env',
)
register(
    id='perennial-lnpk-v0',
    entry_point='wofost_gym.envs.wofost_perennail:Perennial_Limited_NPK_Env',
)
register(
    id='perennial-ln-v0',
    entry_point='wofost_gym.envs.wofost_perennail:Perennial_Limited_N_Env',
)
register(
    id='perennial-lnw-v0',
    entry_point='wofost_gym.envs.wofost_perennail:Perennial_Limited_NW_Env',
)
register(
    id='perennial-lw-v0',
    entry_point='wofost_gym.envs.wofost_perennail:Perennial_Limited_W_Env',
)

# Perennial Harvest Environments
register(
    id='perennial-harvest-npk-v0',
    entry_point='wofost_gym.envs.plant_perennial:Perennail_Harvest_LNPKW_Env',
)
register(
    id='perennial-harvest-pp-v0',
    entry_point='wofost_gym.envs.plant_perennial:Perennail_Harvest_PP_Env',
)
register(
    id='perennial-harvest-lnpk-v0',
    entry_point='wofost_gym.envs.plant_perennial:Perennail_Harvest_Limited_NPK_Env',
)
register(
    id='perennial-harvest-ln-v0',
    entry_point='wofost_gym.envs.plant_perennial:Perennail_Harvest_Limited_N_Env',
)
register(
    id='perennial-harvest-lnw-v0',
    entry_point='wofost_gym.envs.plant_perennial:Perennail_Harvest_Limited_NW_Env',
)
register(
    id='perennial-harvest-lw-v0',
    entry_point='wofost_gym.envs.plant_perennial:Perennail_Harvest_Limited_W_Env',
)