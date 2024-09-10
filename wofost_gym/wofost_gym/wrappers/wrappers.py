import gymnasium as gym
import numpy as np
from gymnasium.spaces import Dict, Discrete, Box

from wofost_gym.envs.wofost import NPK_Env
from wofost_gym.envs.wofost import PP_Env
from wofost_gym.envs.wofost import Limited_NPK_Env
from wofost_gym.envs.wofost import Limited_N_Env
from wofost_gym.envs.wofost import Limited_NW_Env
from wofost_gym.envs.wofost import Limited_W_Env

from wofost_gym.envs.wofost_harvest import Harvest_NPK_Env
from wofost_gym.envs.wofost_harvest import Harvest_PP_Env
from wofost_gym.envs.wofost_harvest import Harvest_Limited_NPK_Env
from wofost_gym.envs.wofost_harvest import Harvest_Limited_N_Env
from wofost_gym.envs.wofost_harvest import Harvest_Limited_NW_Env
from wofost_gym.envs.wofost_harvest import Harvest_Limited_W_Env




# Action Enums
N_ACT = 0
P_ACT = 1
K_ACT = 2
W_ACT = 3


# Wrapper class to output a dictionary instead of a flat space
# Useful for handcrafted human-readable policies
class NPKDictWrapper(gym.ObservationWrapper):
    def __init__(self, env):
        super().__init__(env)
        self.env = env
        self.output_vars = env.unwrapped.args.output_vars

        self.weather_vars = env.unwrapped.args.weather_vars
        if env.unwrapped.forecast_length > 1:
            self.forecast_vars = []
            for i in range(1, env.unwrapped.forecast_length):
                self.forecast_vars += [s + f"_{i+1}" for s in self.weather_vars]
        self.forecast_vars += self.weather_vars 

        output_dict = [(ov, Box(low=-np.inf, high=np.inf,shape=(1,))) for ov in self.output_vars]
        weather_dict = [(wv, Box(low=-np.inf, high=np.inf,shape=(1,))) for wv in self.output_vars]

        self.observation_space = Dict(dict(output_dict+weather_dict+\
                                           [("DAYS", Box(low=-np.inf, high=np.inf,shape=(1,)))]))

    def observation(self, obs):
        keys = self.output_vars + self.forecast_vars + ["DAYS"]
        return dict([(keys[i], obs[i]) for i in range(len(keys))])


# Wrapper class to turn a MultiDiscrete NPK Env to a Discrete Action Env
# TODO: Fix this wrapper
class NPKDictActionWrapper(gym.ActionWrapper):
    def __init__(self, env):
        super().__init__(env)
        self.env = env

        # harvesting environments
        if isinstance(env, Harvest_NPK_Env):
            if isinstance(env, Harvest_PP_Env):
                self.action_space = gym.spaces.Dict({"plant": Discrete(1), "harvest": Discrete(1)})
            elif isinstance(env, Harvest_Limited_NPK_Env):
                self.action_space = gym.spaces.Dict({"plant": Discrete(1), "harvest": Discrete(1), \
                                 "n": Discrete(env.unwrapped.num_fert),\
                                 "p": Discrete(env.unwrapped.num_fert),\
                                 "k": Discrete(env.unwrapped.num_fert)})
            elif isinstance(env, Harvest_Limited_N_Env):
                self.action_space = gym.spaces.Dict({"plant": Discrete(1), "harvest": Discrete(1), \
                                 "n": Discrete(env.unwrapped.num_fert)})
            elif isinstance(env, Harvest_Limited_NW_Env):
                self.action_space = gym.spaces.Dict({"plant": Discrete(1), "harvest": Discrete(1), \
                                 "n": Discrete(env.unwrapped.num_fert),\
                                 "irrig": Discrete(env.unwrapped.num_irrig)})
            elif isinstance(env, Harvest_Limited_W_Env):
                self.action_space = gym.spaces.Dict({"plant": Discrete(1), "harvest": Discrete(1), \
                                 "irrig": Discrete(env.unwrapped.num_irrig)})
            else: 
                self.action_space = gym.spaces.Dict({"plant": Discrete(1), "harvest": Discrete(1), \
                                 "n": Discrete(env.unwrapped.num_fert),\
                                 "p": Discrete(env.unwrapped.num_fert),\
                                 "k": Discrete(env.unwrapped.num_fert),\
                                 "irrig": Discrete(env.unwrapped.num_irrig)})

        # Default environments
        else: 
            if isinstance(env, PP_Env):
                self.action_space = gym.spaces.Dict({"n": Discrete(1)})
            elif isinstance(env, Limited_NPK_Env):
                self.action_space = gym.spaces.Dict({"n": Discrete(env.unwrapped.num_fert),\
                                 "p": Discrete(env.unwrapped.num_fert),\
                                 "k": Discrete(env.unwrapped.num_fert)})
            elif isinstance(env, Limited_N_Env):
                self.action_space = gym.spaces.Dict({"n": Discrete(env.unwrapped.num_fert)})
            elif isinstance(env, Limited_NW_Env):
                self.action_space = gym.spaces.Dict({"n": Discrete(env.unwrapped.num_fert),\
                                 "irrig": Discrete(env.unwrapped.num_irrig)})
            elif isinstance(env, Limited_W_Env):
                self.action_space = gym.spaces.Dict({"irrig": Discrete(env.unwrapped.num_irrig)})
            else: 
                self.action_space = gym.spaces.Dict({"n": Discrete(env.unwrapped.num_fert),\
                                 "p": Discrete(env.unwrapped.num_fert),\
                                 "k": Discrete(env.unwrapped.num_fert),\
                                 "irrig": Discrete(env.unwrapped.num_irrig)})

    def action(self, act):
        print(act)
        return act
 
# TODO: Fix this wrapper
class RewardFertilizationCostWrapper(gym.Wrapper):
    def __init__(self, env):
        super().__init__(env)
        self.env = env

    def step(self, action):
        npk, irrigation = self.env.unwrapped._take_action(action)
        output = self.env.unwrapped._run_simulation()

        obs = self.env.unwrapped._process_output(output)
        self.date = output.index[-1]
        reward = output.iloc[-1]['GWSO']
        done = self.date >= self.env.unwrapped.crop_end_date

        self.env.unwrapped._log(output.iloc[-1]['GWSO'], npk, irrigation, reward)

        #TODO Truncations and crop signals
        truncation = False

        return obs, reward, done, truncation, self.env.unwrapped.log
    
     # Get reward from the simulation
    def _get_reward(self, output, action):
        n_amount = self.fert_amount * action[1] * (action[0] == N_ACT)
        p_amount = self.fert_amount * action[1] * (action[0] == P_ACT)
        k_amount = self.fert_amount * action[1] * (action[0] == K_ACT)
        irrig_amount = self.irrig_amount * action[1] * (action[0] == W_ACT)
        reward = output.iloc[-1]['GWSO'] - \
                        (np.sum(self.beta * np.array([n_amount, p_amount, k_amount])))
        return reward
    
    def reset(self, **kwargs):
        return self.env.reset(**kwargs)
    
# TODO: Fix this wrapper     
class RewardFertilizationThresholdWrapper(gym.Wrapper):
    def __init__(self, env):
        super().__init__(env)
        self.env = env

    def step(self, action):
        npk, irrigation = self.env.unwrapped._take_action(action)
        output = self.env.unwrapped._run_simulation()

        obs = self.env.unwrapped._process_output(output)
        self.date = output.index[-1]
        reward = self._get_reward(output, action)
        done = self.date >= self.env.unwrapped.crop_end_date

        self.env.unwrapped._log(output.iloc[-1]['GWSO'], npk, irrigation, reward)

        #TODO Truncations and crop signals
        truncation = False

        return obs, reward, done, truncation, self.env.unwrapped.log
    
     # Get reward from the simulation
    def _get_reward(self, output, action):
        # Return high negative reward if we apply more nutrient after the threshold is 
        # already passed
        if output.iloc[-1]['TOTN'] > self.max_n and action[0] == envs.N_ACT and action[1] > 0:
            return -1e5
        if output.iloc[-1]['TOTP'] > self.max_p and action[0] == envs.P_ACT and action[1] > 0:
            return -1e5
        if output.iloc[-1]['TOTK'] > self.max_k and action[0] == envs.K_ACT and action[1] > 0:
            return -1e5
        if output.iloc[-1]['TOTIRRIG'] > self.max_w and action[0] == envs.W_ACT and action[1] > 0 : 
            return -1e5
        
        return output.iloc[-1]['GWSO']
    
    def reset(self, **kwargs):
        return self.env.reset(**kwargs)