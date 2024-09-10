# Written 2024, by Will Solow
# A file contanining many different fertilization and irrigation policies
# 

from wofost_gym.utils import PolicyException
from abc import abstractmethod

class Policy:
    required_vars = list
    def __init__(self, env, required_vars=[]):
        self.required_vars = required_vars
        self.env = env.unwrapped
    
    # Call policy passing observation
    def __call__(self,obs):
        # Check that required 
        if isinstance(obs, dict):
            self._validate(obs)
        
        return self._get_action(obs)
    
    def _validate(self,obs):
        for key in self.required_vars:
            if not key in list(obs.keys()):
                msg = "Required observation for policy is not in inputted observation "
                raise PolicyException(msg)

    @abstractmethod     
    def _get_action(self,obs):
        msg = "Policy Subclass should implement this"
        raise NotImplementedError(msg) 

# Default policy, which performs no irrigation or fertilization action
class No_Action(Policy):
    def __init__(self, required_vars=[]):
        super().__init__(required_vars)

    def _get_action(self, obs):
        return {'n': 0, 'p': 0, 'k': 0, 'irrig':0 }
    
class Weekly_N(Policy):
    def __init__(self, env, amount=0, required_vars=[]):
        super().__init__(env, required_vars)
        self.amount = amount

    def _validate(self, obs):
        if self.amount > self.env.num_fert:
            msg = "N Amount exceeds total Nitrogen actions"
            raise PolicyException(msg)
        for key in self.required_vars:
            if not key in list(obs.keys()):
                msg = "Required observation for policy is not in inputted observation "
                raise PolicyException(msg)
        

    def _get_action(self, obs):
        return {'n': self.amount, 'p': 0, 'k': 0, 'irrig':0 }

# Default policy, which performs no irrigation or fertilization action
class No_Action_Harvest(Policy):
    def __init__(self, required_vars=[]):
        super().__init__(required_vars)

    def _get_action(self, obs):
        print(obs[-1])
        if obs[-1] == 30:
            return {'plant': 1, 'harvest': 0, 'n': 0, 'p': 0, 'k': 0, 'irrig':0 }
        if obs[-1] == 225:
            return {'plant': 0, 'harvest': 1, 'n': 0, 'p': 0, 'k': 0, 'irrig':0 }
        
        return {'plant': 0, 'harvest': 0, 'n': 0, 'p': 0, 'k': 0, 'irrig':0 }
