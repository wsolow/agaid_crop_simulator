import gymnasium as gym
import numpy as np
import wofost_gym.envs.npk_env as npk_env

# Wrapper class to turn a MultiDiscrete NPK Env to a Discrete Action Env
class npk_discrete(gym.ActionWrapper):
    def __init__(self, env):
        super().__init__(env)
        self.num_n = env.unwrapped.num_n
        self.num_p = env.unwrapped.num_p
        self.num_k = env.unwrapped.num_k
        self.num_irrig = env.unwrapped.num_irrig
        self.num_actions = env.unwrapped.num_actions
        self.action_space = gym.spaces.Discrete(4 * self.num_actions)

    def action(self, act):
        action = np.array([0,0])
        action[0] = act // self.num_actions
        action[1] = act % self.num_actions

        # Clip actions if larger than specified
        if action[0] == npk_env.N_ACT:
            action[1] = np.minimum(action[1], self.num_n-1)
        elif action[0] == npk_env.P_ACT:
            action[1] = np.minimum(action[1], self.num_p-1)
        elif action[0] == npk_env.K_ACT:
            action[1] = np.minimum(action[1], self.num_k-1)
        elif action[0] == npk_env.W_ACT:
            action[1] = np.minimum(action[1], self.num_irrig-1)

        return action
        
    '''def action(self, act):
        action = np.array([0,0,0,0])
        action[0] = act // (self.num_p * self.num_k * self.num_irrig)
        action[1] = (act % (self.num_p * self.num_k * self.num_irrig)) // (self.num_k*self.num_irrig)
        action[2] = (act % (self.num_k * self.num_irrig)) // (self.num_irrig)
        action[3] = act % self.num_irrig
        return action'''