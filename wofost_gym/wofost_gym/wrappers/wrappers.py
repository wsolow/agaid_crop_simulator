import gymnasium as gym
import numpy as np
import wofost_gym.envs.wofost_envs as envs

# Action Enums
N_ACT = 0
P_ACT = 1
K_ACT = 2
W_ACT = 3


# Wrapper class to turn a MultiDiscrete NPK Env to a Discrete Action Env
class NPKDiscreteWrapper(gym.ActionWrapper):
    def __init__(self, env):
        super().__init__(env)
        self.env = env
        self.num_n = env.unwrapped.num_n
        self.num_p = env.unwrapped.num_p
        self.num_k = env.unwrapped.num_k
        self.num_irrig = env.unwrapped.num_irrig
        self.num_actions = env.unwrapped.num_actions
        self.action_space = gym.spaces.Discrete(4 * self.num_actions)
    
    def reset(self, **kwargs):
        return self.env.reset(**kwargs)
    

    def action(self, act):
        action = np.array([0,0])
        action[0] = act // self.num_actions
        action[1] = act % self.num_actions

        # Clip actions if larger than specified
        if action[0] == envs.N_ACT:
            action[1] = np.minimum(action[1], self.num_n-1)
        elif action[0] == envs.P_ACT:
            action[1] = np.minimum(action[1], self.num_p-1)
        elif action[0] == envs.K_ACT:
            action[1] = np.minimum(action[1], self.num_k-1)
        elif action[0] == envs.W_ACT:
            action[1] = np.minimum(action[1], self.num_irrig-1)

        return action
 

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