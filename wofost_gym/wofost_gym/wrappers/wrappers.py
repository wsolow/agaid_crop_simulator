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

from wofost_gym.utils import ActionException




# Action Enums
N_ACT = 0
P_ACT = 1
K_ACT = 2
W_ACT = 3


# Wrapper class to output a dictionary instead of a flat space
# Useful for handcrafted human-readable policies
class NPKDictObservationWrapper(gym.ObservationWrapper):
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
        self.num_fert = env.unwrapped.num_fert
        self.num_irrig = env.unwrapped.num_irrig
        # harvesting environments
        if isinstance(env.unwrapped, Harvest_NPK_Env):
            if isinstance(env, Harvest_PP_Env):
                self.action_space = gym.spaces.Dict({"null": Discrete(1), \
                                 "plant": Discrete(1), "harvest": Discrete(1)})
            elif isinstance(env.unwrapped, Harvest_Limited_NPK_Env):
                self.action_space = gym.spaces.Dict({"null": Discrete(1), \
                                 "plant": Discrete(1), "harvest": Discrete(1), \
                                 "n": Discrete(env.unwrapped.num_fert),\
                                 "p": Discrete(env.unwrapped.num_fert),\
                                 "k": Discrete(env.unwrapped.num_fert)})
            elif isinstance(env.unwrapped, Harvest_Limited_N_Env):
                self.action_space = gym.spaces.Dict({"null": Discrete(1), \
                                 "plant": Discrete(1), "harvest": Discrete(1), \
                                 "n": Discrete(env.unwrapped.num_fert)})
            elif isinstance(env.unwrapped, Harvest_Limited_NW_Env):
                self.action_space = gym.spaces.Dict({"null": Discrete(1), \
                                 "plant": Discrete(1), "harvest": Discrete(1), \
                                 "n": Discrete(env.unwrapped.num_fert),\
                                 "irrig": Discrete(env.unwrapped.num_irrig)})
            elif isinstance(env.unwrapped, Harvest_Limited_W_Env):
                self.action_space = gym.spaces.Dict({"null": Discrete(1), \
                                 "plant": Discrete(1), "harvest": Discrete(1), \
                                 "irrig": Discrete(env.unwrapped.num_irrig)})
            else: 
                self.action_space = gym.spaces.Dict({"null": Discrete(1), \
                                 "plant": Discrete(1), "harvest": Discrete(1), \
                                 "n": Discrete(env.unwrapped.num_fert),\
                                 "p": Discrete(env.unwrapped.num_fert),\
                                 "k": Discrete(env.unwrapped.num_fert),\
                                 "irrig": Discrete(env.unwrapped.num_irrig)})

        # Default environments
        else: 
            if isinstance(env.unwrapped, PP_Env):
                self.action_space = gym.spaces.Dict({"null": Discrete(1), "n": Discrete(1)})
            elif isinstance(env.unwrapped, Limited_NPK_Env):
                self.action_space = gym.spaces.Dict({"null": Discrete(1),\
                                 "n": Discrete(env.unwrapped.num_fert),\
                                 "p": Discrete(env.unwrapped.num_fert),\
                                 "k": Discrete(env.unwrapped.num_fert)})
            elif isinstance(env.unwrapped, Limited_N_Env):
                self.action_space = gym.spaces.Dict({"null": Discrete(1),\
                                 "n": Discrete(env.unwrapped.num_fert)})
            elif isinstance(env.unwrapped, Limited_NW_Env):
                self.action_space = gym.spaces.Dict({"null": Discrete(1),\
                                 "n": Discrete(env.unwrapped.num_fert),\
                                 "irrig": Discrete(env.unwrapped.num_irrig)})
            elif isinstance(env.unwrapped, Limited_W_Env):
                self.action_space = gym.spaces.Dict({"null": Discrete(1),\
                                 "irrig": Discrete(env.unwrapped.num_irrig)})
            else: 
                self.action_space = gym.spaces.Dict({"null": Discrete(1),\
                                 "n": Discrete(env.unwrapped.num_fert),\
                                 "p": Discrete(env.unwrapped.num_fert),\
                                 "k": Discrete(env.unwrapped.num_fert),\
                                 "irrig": Discrete(env.unwrapped.num_irrig)})

    def action(self, act):
        if not isinstance(act, dict):
            msg = "Action must be of dictionary type. See README for more information"
            raise ActionException(msg)
        else: 
            act_vals = list(act.values())
            for v in act_vals:
                if not isinstance(v, int):
                    msg = "Action value must be of type int"
                    raise ActionException(msg)
            if len(np.nonzero(act_vals)[0]) > 1:
                msg = "More than one non-zero action value for policy"
                raise ActionException(msg)
            # If no actions specified, assume that we mean the null action
            if len(np.nonzero(act_vals)[0]) == 0:
                return 0
        
        if not "n" in act.keys():
            msg = "Nitrogen action \'n\' not included in action dictionary keys"
            raise ActionException(msg)
        if not "p" in act.keys():
            msg = "Phosphorous action \'p\' not included in action dictionary keys"
            raise ActionException(msg)
        if not "k" in act.keys():
            msg = "Potassium action \'k\' not included in action dictionary keys"
            raise ActionException(msg)
        if not "irrig" in act.keys():
            msg = "Irrigation action \'irrig\' not included in action dictionary keys"
            raise ActionException(msg)

        # harvesting environments
        if isinstance(self.env.unwrapped, Harvest_NPK_Env):
            # Check for planting and harvesting actions
            if not "plant" in act.keys():
                msg = "\'plant\' not included in action dictionary keys"
                raise ActionException(msg)
            if not "harvest" in act.keys():
                msg = "\'harvest\' not included in action dictionary keys"
                raise ActionException(msg)
            if len(act.keys()) != 6:
                msg = "Incorrect action dictionary specification"
                raise ActionException(msg)
            
            # Set the offsets to support converting to the correct action
            offsets = [1,1,self.num_fert,self.num_fert,self.num_fert,self.num_irrig]
            act_values = [act["plant"],act["harvest"],act["n"],act["p"],act["k"],act["irrig"]]
            offset_flags = np.zeros(6)
            offset_flags[:np.nonzero(act_values)[0][0]] = 1
        
            if isinstance(self.env.unwrapped, Harvest_PP_Env):
                return np.sum(offsets*offset_flags) + act_values[np.nonzero(act_values)[0][0]] 
            elif isinstance(self.env.unwrapped, Harvest_Limited_NPK_Env):
                return np.sum(offsets*offset_flags) + act_values[np.nonzero(act_values)[0][0]] 
            elif isinstance(self.env.unwrapped, Harvest_Limited_N_Env):
                return np.sum(offsets*offset_flags) + act_values[np.nonzero(act_values)[0][0]] 
            elif isinstance(self.env.unwrapped, Harvest_Limited_NW_Env):
                return np.sum(offsets*offset_flags) + act_values[np.nonzero(act_values)[0][0]] 
            elif isinstance(self.env.unwrapped, Harvest_Limited_W_Env):
                return np.sum(offsets*offset_flags) + act_values[np.nonzero(act_values)[0][0]] 
            else: 
                return np.sum(offsets*offset_flags) + act_values[np.nonzero(act_values)[0][0]] 
            
        # Default environments
        else: 
            if len(act.keys()) != 4:
                msg = "Incorrect action dictionary specification"
                raise ActionException(msg)
            # Set the offsets to support converting to the correct action
            offsets = [self.num_fert,self.num_fert,self.num_fert,self.num_irrig]
            act_values = [act["n"],act["p"],act["k"],act["irrig"]]
            offset_flags = np.zeros(4)
            offset_flags[:np.nonzero(act_values)[0][0]] = 1

            if isinstance(self.env.unwrapped, PP_Env):
                return np.sum(offsets*offset_flags) + act_values[np.nonzero(act_values)[0][0]] 
            elif isinstance(self.env.unwrapped, Limited_NPK_Env):
                return np.sum(offsets*offset_flags) + act_values[np.nonzero(act_values)[0][0]] 
            elif isinstance(self.env.unwrapped, Limited_N_Env):
                return np.sum(offsets*offset_flags) + act_values[np.nonzero(act_values)[0][0]] 
            elif isinstance(self.env.unwrapped, Limited_NW_Env):
                return np.sum(offsets*offset_flags) + act_values[np.nonzero(act_values)[0][0]] 
            elif isinstance(self.env.unwrapped, Limited_W_Env):
                return np.sum(offsets*offset_flags) + act_values[np.nonzero(act_values)[0][0]] 
            else: 
                return np.sum(offsets*offset_flags) + act_values[np.nonzero(act_values)[0][0]] 

        
 

 
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