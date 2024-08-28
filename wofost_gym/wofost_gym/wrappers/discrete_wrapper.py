import gymnasium as gym
import numpy as np

# Wrapper class to turn a MultiDiscrete NPK Env to a Discrete Action Env
class npk_discrete(gym.ActionWrapper):
    def __init__(self, env):
        super().__init__(env)
        self.num_n = env.unwrapped.num_n
        self.num_p = env.unwrapped.num_p
        self.num_k = env.unwrapped.num_k
        self.num_irrig = env.unwrapped.num_irrig
        self.action_space = gym.spaces.Discrete(self.num_n*self.num_p*self.num_k*self.num_irrig)

    def action(self, act):
        action = np.array([0,0,0,0])
        action[0] = act // (self.num_p * self.num_k * self.num_irrig)
        action[1] = (act % (self.num_p * self.num_k * self.num_irrig)) // (self.num_k*self.num_irrig)
        action[2] = (act % (self.num_k * self.num_irrig)) // (self.num_irrig)
        action[3] = act % self.num_irrig
        return action