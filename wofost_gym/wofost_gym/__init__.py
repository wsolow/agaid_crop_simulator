from gymnasium.envs.registration import register
from . import utils

register(
    id='wofost-v0',
    entry_point='wofost_gym.envs.wofost:NPK_Env',
)

register(
    id='pp-v0',
    entry_point='wofost_gym.envs.wofost:PP_Env',
)

register(
    id='limited_npk-v0',
    entry_point='wofost_gym.envs.wofost:Limited_NPK_Env',
)
register(
    id='limited_n-v0',
    entry_point='wofost_gym.envs.wofost:Limited_N_Env',
)
register(
    id='limited_nw-v0',
    entry_point='wofost_gym.envs.wofost:Limited_NW_Env',
)
register(
    id='limited_w-v0',
    entry_point='wofost_gym.envs.wofost:Limited_W_Env',
)

