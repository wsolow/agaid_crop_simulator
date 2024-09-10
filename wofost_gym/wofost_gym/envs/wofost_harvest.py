import os
import datetime
import numpy as np
import pandas as pd
import yaml

import gymnasium as gym
import pcse
from pathlib import Path
import pcse.engine

from .. import utils

from .wofost import NPK_Env

from pcse.soil.soil_wrappers import SoilModuleWrapper_LNPKW
from  pcse.soil.soil_wrappers import SoilModuleWrapper_LN
from  pcse.soil.soil_wrappers import SoilModuleWrapper_LNPK
from  pcse.soil.soil_wrappers import SoilModuleWrapper_PP
from  pcse.soil.soil_wrappers import SoilModuleWrapper_LW
from  pcse.soil.soil_wrappers import SoilModuleWrapper_LNW
from pcse.crop.wofost8 import Wofost80
from pcse.agromanager import AgroManagerHarvest


# Base model simulating growth of crop subject to NPK and water limited dynamics
class Harvest_NPK_Env(NPK_Env):
    config = utils.make_config()
    config['SOIL'] = SoilModuleWrapper_LNPKW
    config['CROP'] = Wofost80
    config['AGROMANAGEMENT'] = AgroManagerHarvest

    def __init__(self, args):
        super().__init__(args)

        self.crop_name = self.agromanagement['CropCalendar']['crop_name']
        self.variety_name = self.agromanagement['CropCalendar']['variety_name']
        self.crop_start_type = self.agromanagement['CropCalendar']['crop_start_type']
        self.crop_end_type = self.agromanagement['CropCalendar']['crop_end_type']
        self.active_crop_flag = False

        self.action_space = gym.spaces.Discrete(3+3*args.num_fert+args.num_irrig)

    # Send action to the model
    def _take_action(self, action):
        p_act = 0
        h_act = 0
        n_amount = 0
        p_amount = 0
        k_amount = 0
        irrig_amount = 0

        # Null Action
        if action == 0:
            return (p_act, h_act, n_amount, p_amount, k_amount, irrig_amount)
        
        # Planting action
        elif action == 1:
            if not self.active_crop_flag:
                self.model._send_signal(signal=pcse.signals.crop_start, crop_name= \
                            self.crop_name, variety_name=self.variety_name, \
                            crop_start_type=self.crop_start_type, crop_end_type=\
                            self.crop_end_type, day=self.date)
                self.active_crop_flag = True
            p_act = 1
            return (p_act, h_act, n_amount, p_amount, k_amount, irrig_amount)
        
        # Harvesting Action
        elif action == 2:
            if self.active_crop_flag:
                self.model._send_signal(signal=pcse.signals.crop_harvest, day=self.date,\
                                        effiency=self.harvest_effec)
            h_act=1
            return (p_act, h_act, n_amount, p_amount, k_amount, irrig_amount)

         # Irrigation action
        if action >= 3 * self.num_fert+3:
            i_amount = action - (3 * self.num_fert)-2
            i_amount *= self.irrig_amount
            self.model._send_signal(signal=pcse.signals.irrigate, amount=i_amount, \
                                    efficiency=self.irrig_effec)
            return (p_act, h_act, n_amount, p_amount, k_amount, irrig_amount)
        
        # Fertilizaiton action, correct for 2 crop specific actions (harvest/plant) and null action
        if action >= 3:
            action -= 3
            # Nitrogen fertilization
            if action // self.num_fert == 0:
                n_amount = self.fert_amount * ((action % self.num_fert) + 1) 
                self.model._send_signal(signal=pcse.signals.apply_npk, \
                                        N_amount=n_amount, N_recovery=self.n_recovery)
            elif action // self.num_fert == 1:
                p_amount = self.fert_amount * ((action % self.num_fert) + 1) 
                self.model._send_signal(signal=pcse.signals.apply_npk, \
                                        P_amount=p_amount, P_recovery=self.p_recovery)
            elif action // self.num_fert == 2:
                k_amount = self.fert_amount * ((action % self.num_fert) + 1) 
                self.model._send_signal(signal=pcse.signals.apply_npk, \
                                        K_amount=k_amount, K_recovery=self.k_recovery)
                
        return (p_act, h_act, n_amount, p_amount, k_amount, irrig_amount)

    def _init_log(self):
        return {'growth': dict(), 'plant': dict(), 'harvest': dict(), 'nitrogen': dict(), \
                'phosphorous': dict(), 'potassium': dict(), 'irrigation':dict(), 'reward': dict(), 'day':dict()}
    
    def _log(self, growth, action, reward):
        self.log['growth'][self.date] = growth
        self.log['plant'][self.date] = action[0]
        self.log['harvest'][self.date] = action[1]
        self.log['nitrogen'][self.date - datetime.timedelta(self.intervention_interval)] = \
            action[2]
        self.log['phosphorous'][self.date - datetime.timedelta(self.intervention_interval)] = \
            action[3]
        self.log['potassium'][self.date - datetime.timedelta(self.intervention_interval)] = \
            action[4]
        self.log['irrigation'][self.date - datetime.timedelta(self.intervention_interval)] = \
            action[5]
        self.log['reward'][self.date] = reward
        self.log['day'][self.date] = self.date  


# Simulating Potential Production - useful for seeing how much the crop
# could grow without water limiting conditions
class Harvest_PP_Env(Harvest_NPK_Env):
    # Set config
    config = utils.make_config()
    config['SOIL'] = SoilModuleWrapper_PP
    config['CROP'] = Wofost80
    config['AGROMANAGEMENT'] = AgroManagerHarvest
    def __init__(self, args):
        super().__init__(args)

        self.action_space = gym.spaces.Discrete(3)

    # Send action to the model
    def _take_action(self, action):
        p_act = 0
        h_act = 0

        # Null Action
        if action == 0:
            return (p_act, h_act, 0, 0, 0, 0)
        
        # Planting action
        elif action == 1:
            if not self.active_crop_flag:
                self.model._send_signal(signal=pcse.signals.crop_start, crop_name= \
                            self.crop_name, variety_name=self.variety_name, \
                            crop_start_type=self.crop_start_type, crop_end_type=\
                            self.crop_end_type, day=self.date)
                self.active_crop_flag = True
            p_act = 1
            return (p_act, h_act, 0, 0, 0, 0)
        
        # Harvesting Action
        elif action == 2:
            if self.active_crop_flag:
                self.model._send_signal(signal=pcse.signals.crop_harvest, day=self.date,\
                                        effiency=self.harvest_effec)
            h_act=1
            return (p_act, h_act, 0, 0, 0, 0)


# Simulating production under abundant water but limited NPK dynamics
class Harvest_Limited_NPK_Env(Harvest_NPK_Env):
    config = utils.make_config()
    config['SOIL'] = SoilModuleWrapper_LNPK
    config['CROP'] = Wofost80
    config['AGROMANAGEMENT'] = AgroManagerHarvest
    def __init__(self, args):
        super().__init__(args)

        self.action_space = gym.spaces.discrete(3+3*self.num_fert)

    # Send action to the model
    def _take_action(self, action):
        p_act = 0
        h_act = 0
        n_amount = 0
        p_amount = 0
        k_amount = 0

        # Null Action
        if action == 0:
            return (p_act, h_act, n_amount, p_amount, k_amount, 0)
        
        # Planting action
        elif action == 1:
            if not self.active_crop_flag:
                self.model._send_signal(signal=pcse.signals.crop_start, crop_name= \
                            self.crop_name, variety_name=self.variety_name, \
                            crop_start_type=self.crop_start_type, crop_end_type=\
                            self.crop_end_type, day=self.date)
                self.active_crop_flag = True
            p_act = 1
            return (p_act, h_act, n_amount, p_amount, k_amount, 0)
        
        # Harvesting Action
        elif action == 2:
            if self.active_crop_flag:
                self.model._send_signal(signal=pcse.signals.crop_harvest, day=self.date,\
                                        effiency=self.harvest_effec)
            h_act=1
            return (p_act, h_act, n_amount, p_amount, k_amount, 0)

        # Fertilizaiton action, correct for 2 crop specific actions (harvest/plant) and null action
        if action >= 3:
            action -= 3
            # Nitrogen fertilization
            if action // self.num_fert == 0:
                n_amount = self.fert_amount * ((action % self.num_fert) + 1) 
                self.model._send_signal(signal=pcse.signals.apply_npk, \
                                        N_amount=n_amount, N_recovery=self.n_recovery)
            elif action // self.num_fert == 1:
                p_amount = self.fert_amount * ((action % self.num_fert) + 1) 
                self.model._send_signal(signal=pcse.signals.apply_npk, \
                                        P_amount=p_amount, P_recovery=self.p_recovery)
            elif action // self.num_fert == 2:
                k_amount = self.fert_amount * ((action % self.num_fert) + 1) 
                self.model._send_signal(signal=pcse.signals.apply_npk, \
                                        K_amount=k_amount, K_recovery=self.k_recovery)
                
        return (p_act, h_act, n_amount, p_amount, k_amount, 0)
        
       
# Simulating production under limited Nitrogen but abundant water and P/K
class Harvest_Limited_N_Env(Harvest_NPK_Env):
    config = utils.make_config()
    config['SOIL'] = SoilModuleWrapper_LN
    config['CROP'] = Wofost80
    config['AGROMANAGEMENT'] = AgroManagerHarvest
    def __init__(self, args):
        super().__init__(args)

        self.action_space = gym.spaces.Discrete(3+self.num_fert)

    # Send action to the model
    def _take_action(self, action):
        p_act = 0
        h_act = 0
        n_amount = 0

        # Null Action
        if action == 0:
            return (p_act, h_act, n_amount, 0, 0, 0)
        
        # Planting action
        elif action == 1:
            if not self.active_crop_flag:
                self.model._send_signal(signal=pcse.signals.crop_start, crop_name= \
                            self.crop_name, variety_name=self.variety_name, \
                            crop_start_type=self.crop_start_type, crop_end_type=\
                            self.crop_end_type, day=self.date)
                self.active_crop_flag = True
            p_act = 1
            return (p_act, h_act, n_amount, 0, 0, 0)
        
        # Harvesting Action
        elif action == 2:
            if self.active_crop_flag:
                self.model._send_signal(signal=pcse.signals.crop_harvest, day=self.date,\
                                        effiency=self.harvest_effec)
            h_act=1
            return (p_act, h_act, n_amount, 0, 0, 0)

        
        # Fertilizaiton action, correct for 2 crop specific actions (harvest/plant) and null action
        if action >= 3:
            action -= 3
            # Nitrogen fertilization
            if action // self.num_fert == 0:
                n_amount = self.fert_amount * ((action % self.num_fert) + 1) 
                self.model._send_signal(signal=pcse.signals.apply_npk, \
                                        N_amount=n_amount, N_recovery=self.n_recovery)
                
        return (p_act, h_act, n_amount, 0, 0, 0)


        

# Simulating production under limited water and Nitrogen
class Harvest_Limited_NW_Env(Harvest_NPK_Env):
    config = utils.make_config()
    config['SOIL'] = SoilModuleWrapper_LNW
    config['CROP'] = Wofost80
    config['AGROMANAGEMENT'] = AgroManagerHarvest
    def __init__(self, args):
        super().__init__(args)

        self.action_space = gym.spaces.Discrete(3+self.num_fert + self.num_irrig)

    # Send action to the model
    def _take_action(self, action):
        p_act = 0
        h_act = 0
        n_amount = 0
        irrig_amount = 0

        # Null Action
        if action == 0:
            return (p_act, h_act, n_amount, 0, 0, irrig_amount)
        
        # Planting action
        elif action == 1:
            if not self.active_crop_flag:
                self.model._send_signal(signal=pcse.signals.crop_start, crop_name= \
                            self.crop_name, variety_name=self.variety_name, \
                            crop_start_type=self.crop_start_type, crop_end_type=\
                            self.crop_end_type, day=self.date)
                self.active_crop_flag = True
            p_act = 1
            return (p_act, h_act, n_amount, 0, 0, irrig_amount)
        
        # Harvesting Action
        elif action == 2:
            if self.active_crop_flag:
                self.model._send_signal(signal=pcse.signals.crop_harvest, day=self.date,\
                                        effiency=self.harvest_effec)
            h_act=1
            return (p_act, h_act, n_amount, 0, 0, irrig_amount)

         # Irrigation action
        if action >= 1 * self.num_fert+3:
            i_amount = action - (1 * self.num_fert) - 2
            i_amount *= self.irrig_amount
            self.model._send_signal(signal=pcse.signals.irrigate, amount=i_amount, \
                                    efficiency=self.irrig_effec)
            return (p_act, h_act, n_amount, 0, 0, irrig_amount)
        
        # Fertilizaiton action, correct for 2 crop specific actions (harvest/plant) and null action
        if action >= 3:
            action -= 3
            # Nitrogen fertilization
            if action // self.num_fert == 0:
                n_amount = self.fert_amount * ((action % self.num_fert) + 1) 
                self.model._send_signal(signal=pcse.signals.apply_npk, \
                                        N_amount=n_amount, N_recovery=self.n_recovery)
                
        return (p_act, h_act, n_amount, 0, 0, irrig_amount)


# Simulating production under limited water 
class Harvest_Limited_W_Env(Harvest_NPK_Env):
    config = utils.make_config()
    config['SOIL'] = SoilModuleWrapper_LW
    config['CROP'] = Wofost80
    config['AGROMANAGEMENT'] = AgroManagerHarvest
    def __init__(self, args):
        super().__init__(args)

        self.action_space = gym.spaces.Discrete(2+self.num_irrig)

    # Send action to the model
    def _take_action(self, action):
        p_act = 0
        h_act = 0
        irrig_amount = 0

        # Null Action
        if action == 0:
            return (p_act, h_act, 0, 0, 0, irrig_amount)
        
        # Planting action
        elif action == 1:
            if not self.active_crop_flag:
                self.model._send_signal(signal=pcse.signals.crop_start, crop_name= \
                            self.crop_name, variety_name=self.variety_name, \
                            crop_start_type=self.crop_start_type, crop_end_type=\
                            self.crop_end_type, day=self.date)
                self.active_crop_flag = True
            p_act = 1
            return (p_act, h_act, 0, 0, 0, irrig_amount)
        
        # Harvesting Action
        elif action == 2:
            if self.active_crop_flag:
                self.model._send_signal(signal=pcse.signals.crop_harvest, day=self.date,\
                                        effiency=self.harvest_effec)
            h_act=1
            return (p_act, h_act, 0, 0, 0, irrig_amount)

         # Irrigation action
        if action >= 0 * self.num_fert+3:
            i_amount = action - (0 * self.num_fert) - 2
            i_amount *= self.irrig_amount
            self.model._send_signal(signal=pcse.signals.irrigate, amount=i_amount, \
                                    efficiency=self.irrig_effec)
            return (p_act, h_act, 0, 0, 0, irrig_amount)
        

                
        return (p_act, h_act, 0, 0, 0, irrig_amount)
   
