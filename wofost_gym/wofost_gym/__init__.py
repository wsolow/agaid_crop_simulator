from gymnasium.envs.registration import register

register(
    id='npk-v0',
    entry_point='wofost_gym.envs:NPK_Env',
)



