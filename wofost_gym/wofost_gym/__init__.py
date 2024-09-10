from gymnasium.envs.registration import register
from . import utils

# Vanilla single year envirnoments
register(
    id='npk-v0',
    entry_point='wofost_gym.envs.wofost:NPK_Env',
)
register(
    id='pp-v0',
    entry_point='wofost_gym.envs.wofost:PP_Env',
)
register(
    id='lnpk-v0',
    entry_point='wofost_gym.envs.wofost:Limited_NPK_Env',
)
register(
    id='ln-v0',
    entry_point='wofost_gym.envs.wofost:Limited_N_Env',
)
register(
    id='lnw-v0',
    entry_point='wofost_gym.envs.wofost:Limited_NW_Env',
)
register(
    id='lw-v0',
    entry_point='wofost_gym.envs.wofost:Limited_W_Env',
)

# Single year Harvest Environments
register(
    id='harvest-npk-v0',
    entry_point='wofost_gym.envs.wofost_harvest:Harvest_NPK_Env',
)
register(
    id='harvest-pp-v0',
    entry_point='wofost_gym.envs.wofost_harvest:Harvest_PP_Env',
)
register(
    id='harvest-lnpk-v0',
    entry_point='wofost_gym.envs.wofost_harvest:Harvest_Limited_NPK_Env',
)
register(
    id='harvest-ln-v0',
    entry_point='wofost_gym.envs.wofost_harvest:Harvest_Limited_N_Env',
)
register(
    id='harvest-lnw-v0',
    entry_point='wofost_gym.envs.wofost_harvest:Harvest_Limited_NW_Env',
)
register(
    id='harvest-lw-v0',
    entry_point='wofost_gym.envs.wofost_harvest:Harvest_Limited_W_Env',
)

