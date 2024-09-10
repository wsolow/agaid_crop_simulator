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

from pcse.soil.soil_wrappers import SoilModuleWrapper_LNPKW
from  pcse.soil.soil_wrappers import SoilModuleWrapper_LN
from  pcse.soil.soil_wrappers import SoilModuleWrapper_LNPK
from  pcse.soil.soil_wrappers import SoilModuleWrapper_PP
from  pcse.soil.soil_wrappers import SoilModuleWrapper_LW
from  pcse.soil.soil_wrappers import SoilModuleWrapper_LNW
from pcse.crop.wofost8 import Wofost80
from pcse.agromanager import AgroManagerSingleYear


# Base model simulating growth of crop subject to NPK and water limited dynamics
class NPK_Env(gym.Env):
    config = utils.make_config()
    config['SOIL'] = SoilModuleWrapper_LNPKW
    config['CROP'] = Wofost80
    config['AGROMANAGEMENT'] = AgroManagerSingleYear

    def __init__(self, args):
        self.seed(args.seed)
        self.log = self._init_log()
        self.args = args
        self.wofost_params = args.wf_args
        self.agro_params = args.ag_args

        self.intervention_interval = args.intvn_interval
        self.forecast_length = args.forecast_length
        self.forecast_noise = args.forecast_noise
        self.random_reset = args.random_reset

        # Get the weather and output variables
        self.weather_vars = args.weather_vars
        self.output_vars = args.output_vars
       
        # Load all model parameters from .yaml files
        crop = pcse.fileinput.YAMLCropDataProvider(fpath=os.path.join(args.path, args.crop_fpath))
        site = pcse.fileinput.YAMLSiteDataProvider(fpath=os.path.join(args.path, args.site_fpath))

        self.parameterprovider = pcse.base.ParameterProvider(sitedata=site, cropdata=crop)
        self.agromanagement = self._load_agromanagement_data(os.path.join(args.path, args.agro_fpath))

        # Get information from the agromanagement file
        self.location, self.year = self._load_site_parameters(self.agromanagement)
        self.crop_start_date = self.agromanagement['CropCalendar']['crop_start_date']
        self.crop_end_date = self.agromanagement['CropCalendar']['crop_end_date']
        self.site_start_date = self.agromanagement['SiteCalendar']['site_start_date']
        self.site_end_date = self.agromanagement['SiteCalendar']['site_end_date'] 
        self.year_difference = self.crop_start_date.year - self.site_start_date.year     
        self.max_site_duration = self.site_end_date - self.site_start_date
        self.max_crop_duration = self.crop_end_date - self.crop_start_date

        self.weatherdataprovider = self._get_weatherdataprovider()
        self.train_weather_data = self._get_train_weather_data()
        
        # Override parameters
        utils.set_params(self, self.wofost_params)
        
        # Create crop model
        self.model = pcse.engine.Wofost80(self.parameterprovider, self.weatherdataprovider,
                                         self.agromanagement, config=self.config)
        self.date = self.site_start_date

        
        # NPK/Irrigation action amounts
        self.num_fert = args.num_fert
        self.num_irrig = args.num_irrig
        self.fert_amount = args.fert_amount
        self.irrig_amount = args.irrig_amount

        self.n_recovery = args.n_recovery
        self.p_recovery = args.p_recovery
        self.k_recovery = args.k_recovery
        self.harvest_effec = args.harvest_effec
        self.irrig_effec = args.irrig_effec

        # Thresholds for nutrient application
        self.max_n = args.max_n
        self.max_p = args.max_p
        self.max_k = args.max_k
        self.max_w = args.max_w

        # Create action and observation spaces
        self.action_space = gym.spaces.Discrete(3*self.num_fert + self.num_irrig)
        self.observation_space = gym.spaces.Box(low=-np.inf, high=np.inf, \
                                shape=(1+len(self.output_vars)+len(self.weather_vars)*self.forecast_length,))

    # Load the agromanagement file 
    def _load_agromanagement_data(self, path):
        with open(os.path.join(path)) as file:
            agromanagement = yaml.load(file, Loader=yaml.SafeLoader)
        if "AgroManagement" in agromanagement:
            agromanagement = agromanagement["AgroManagement"]
        
        return utils.set_agro_params(agromanagement, self.agro_params)
    
    # Load the site parameters from agromanagement file
    def _load_site_parameters(self, agromanagement):
        try: 
            site_params = agromanagement['SiteCalendar']
            
            fixed_location = (site_params['latitude'], site_params['longitude'])
            fixed_year = site_params['year']
        except:
            fixed_location = None
            fixed_year = None
        return fixed_location, fixed_year
    
    # Get the historical weather based on the location and year
    def _get_weatherdataprovider(self):
        location = self.location
        if self.location is None:
            latitude = self.np_random.choice([51.5, 52, 52.5])
            longitude = self.np_random.choice([5, 5.5, 6])
            location = (latitude, longitude)
        return pcse.NASAPowerWeatherDataProvider(*location)
    
    # Get the training weather data
    def _get_train_weather_data(self):
        all_years = range(1984, 2018)
        missing_data = []
        train_weather_data = [year for year in all_years if year not in missing_data]
        return train_weather_data
    
    # Get the weather for a range of days
    def _get_weather(self, weatherdataprovider, date, forecast):
        weather_vars = []
        noise_scale = np.linspace(start=self.forecast_noise[0], \
                                  stop=self.forecast_noise[1], num=self.forecast_length)
        for i in range(0, forecast):
            weather = self._get_weather_day(weatherdataprovider, date + datetime.timedelta(i) )

            # Add random noise to weather prediction
            weather += np.random.normal(size=len(weather)) * weather * noise_scale[i] 
            weather_vars.append(weather)
        return np.array(weather_vars)

    # Get the weather for specific date
    def _get_weather_day(self, weatherdataprovider, date):
        weatherdatacontainer = weatherdataprovider(date)
        weather = [getattr(weatherdatacontainer, attr) for attr in self.weather_vars]
        return weather
    
    # Set the seed 
    def seed(self, seed=None):
        self.np_random_seed, seed = gym.utils.seeding.np_random(seed)
        return [seed]
        
    # Render
    def render(self, mode='human', close=False):
        return
    
    # Reset
    def reset(self, **kwargs):
        self.log = self._init_log()

        if 'year' in kwargs:
            self.year = kwargs['year']
        if 'location' in kwargs:
            self.location = kwargs['location']

        # Reset to random year if flag
        if self.random_reset:
            self.year = self.np_random.choice(self.train_weather_data) 
        # Change the current start and end date to specified year
        self.site_start_date = self.site_start_date.replace(year=self.year)
        self.site_end_date = self.site_start_date + self.max_site_duration

        # Correct for if crop start date is in a different year
        self.crop_start_date = self.crop_start_date.replace(year=self.year+self.year_difference)
        self.crop_end_date = self.crop_start_date + self.max_crop_duration
        
        # Change to the new year specified by self.year
        self.date = self.site_start_date

        self.agromanagement['CropCalendar']['crop_start_date'] = self.crop_start_date
        self.agromanagement['CropCalendar']['crop_end_date'] = self.crop_end_date
        self.agromanagement['SiteCalendar']['site_start_date'] = self.site_start_date
        self.agromanagement['SiteCalendar']['site_end_date'] = self.site_end_date
    
        # Reset weather 
        self.weatherdataprovider = self._get_weatherdataprovider()

        # Override parameters
        utils.set_params(self, self.wofost_params)

        # Reset model
        self.model = pcse.engine.Wofost80(self.parameterprovider, self.weatherdataprovider,
                                         self.agromanagement, config=self.config)
        
        # Generate first part of output 
        output = self._run_simulation()
        observation = self._process_output(output)

        return observation, self.log

    # Step through the environment
    def step(self, action):
        act_tuple = self._take_action(action)
        output = self._run_simulation()

        observation = self._process_output(output)
        
        reward = self._get_reward(output, action) 
        
        # Terminate based on site end date
        terminate = self.date >= self.site_end_date
        # Truncate (in some cases) based on the crop end date
        truncation = self.date >= self.crop_end_date

        self._log(output.iloc[-1]['GWSO'], act_tuple, reward)

        #TODO Truncations and crop signals
        truncation = False

        return observation, reward, terminate, truncation, self.log
    
    # Concatenate crop and weather observations
    def _process_output(self, output):
        # Current crop observation
        crop_observation = np.array(output.iloc[-1][self.output_vars])
        self.date = output.index[-1]

        # Observed weather until next intervention time
        weather_observation = self._get_weather(self.weatherdataprovider, self.date,
                                             self.forecast_length)

        # Count the number of days elapsed - useful to have in observation space
        # for time based policies
        days_elapsed = self.date - self.crop_start_date

        observation = np.concatenate([crop_observation, weather_observation.flatten(), [days_elapsed.days]])
        #observation = np.nan_to_num(observation)

        return observation.astype('float32')

    # Run a step in the model
    def _run_simulation(self):
        self.model.run(days=self.intervention_interval)
        output = pd.DataFrame(self.model.get_output()).set_index("day")

        # Gets rid of deprecation warning on fillna
        with pd.option_context("future.no_silent_downcasting", True):
            output = output.fillna(value=np.nan).infer_objects(copy=False)
        return output

    # Send action to the model
    def _take_action(self, action):
        n_amount = 0
        p_amount = 0
        k_amount = 0
        irrig_amount = 0

        # Irrigation action
        if action >= 3 * self.num_fert:
            irrig_amount -= (3 * self.num_fert) 
            self.model._send_signal(signal=pcse.signals.irrigate, amount=irrig_amount, \
                                    efficiency=self.irrig_effec)

        # Fertilizaiton action, correct for 2 crop specific actions (harvest/plant)
        # Nitrogen fertilization
        if action // self.num_fert == 0:
            n_amount = self.fert_amount * (action % self.num_fert) 
            self.model._send_signal(signal=pcse.signals.apply_npk, \
                                    N_amount=n_amount, N_recovery=self.n_recovery)
        elif action // self.num_fert == 1:
            p_amount = self.fert_amount * (action % self.num_fert) 
            self.model._send_signal(signal=pcse.signals.apply_npk, \
                                    P_amount=p_amount, P_recovery=self.p_recovery)
        elif action // self.num_fert == 2:
            k_amount = self.fert_amount * (action % self.num_fert) 
            self.model._send_signal(signal=pcse.signals.apply_npk, \
                                        K_amount=k_amount, K_recovery=self.k_recovery)

        return (n_amount, p_amount, k_amount, irrig_amount)

    # Get reward from the simulation
    def _get_reward(self, output, action):
        '''reward = output.iloc[-1]['WSO'] - \
                        (np.sum(self.beta * np.array([n_amount, p_amount, k_amount])) \
                        - .25 * self.beta * irrig_amount)'''
        reward = output.iloc[-1]['GWSO']
        return reward
        
    def _init_log(self):
        return {'growth': dict(), 'nitrogen': dict(), 'phosphorous': dict(), 'potassium': dict(), 'irrigation':dict(), 'reward': dict(), 'day':dict()}
    
    def _log(self, growth, action, reward):
        self.log['growth'][self.date] = growth
        self.log['nitrogen'][self.date - datetime.timedelta(self.intervention_interval)] = \
            action[0]
        self.log['phosphorous'][self.date - datetime.timedelta(self.intervention_interval)] = \
            action[1]
        self.log['potassium'][self.date - datetime.timedelta(self.intervention_interval)] = \
            action[2]
        self.log['irrigation'][self.date - datetime.timedelta(self.intervention_interval)] = \
            action[3]
        self.log['reward'][self.date] = reward
        self.log['day'][self.date] = self.date  

# Simulating Potential Production - useful for seeing how much the crop
# could grow without water limiting conditions
class PP_Env(NPK_Env):
    # Set config
    config = utils.make_config()
    config['SOIL'] = SoilModuleWrapper_PP
    config['CROP'] = Wofost80
    config['AGROMANAGEMENT'] = AgroManagerSingleYear
    def __init__(self, args):
        super().__init__(args)

        self.action_space = gym.spaces.Discrete(1)

    # Send action to the model
    def _take_action(self, action):
        return (0, 0, 0, 0)


# Simulating production under abundant water but limited NPK dynamics
class Limited_NPK_Env(NPK_Env):
    config = utils.make_config()
    config['SOIL'] = SoilModuleWrapper_LNPK
    config['CROP'] = Wofost80
    config['AGROMANAGEMENT'] = AgroManagerSingleYear

    def __init__(self, args):
        super().__init__(args)

        self.action_space = gym.spaces.discrete(3*self.num_fert)

        # Send action to the model
    def _take_action(self, action):
        n_amount = 0
        p_amount = 0
        k_amount = 0

        # Fertilizaiton action, correct for 2 crop specific actions (harvest/plant)
        # Nitrogen fertilization
        if action // self.num_fert == 0:
            n_amount = self.fert_amount * (action % self.num_fert) 
            self.model._send_signal(signal=pcse.signals.apply_npk, \
                                    N_amount=n_amount, N_recovery=self.n_recovery)
        elif action // self.num_fert == 1:
            p_amount = self.fert_amount * (action % self.num_fert) 
            self.model._send_signal(signal=pcse.signals.apply_npk, \
                                    P_amount=p_amount, P_recovery=self.p_recovery)
        elif action // self.num_fert == 2:
            k_amount = self.fert_amount * (action % self.num_fert) 
            self.model._send_signal(signal=pcse.signals.apply_npk, \
                                        K_amount=k_amount, K_recovery=self.k_recovery)

        return (n_amount, p_amount, k_amount, 0)

# Simulating production under limited Nitrogen but abundant water and P/K
class Limited_N_Env(NPK_Env):
    config = utils.make_config()
    config['SOIL'] = SoilModuleWrapper_LN
    config['CROP'] = Wofost80
    config['AGROMANAGEMENT'] = AgroManagerSingleYear
    def __init__(self, args):
        super().__init__(args)

        self.action_space = gym.spaces.Discrete(self.num_fert)


    def _take_action(self, action):
        n_amount = 0
        # Fertilizaiton action, correct for 2 crop specific actions (harvest/plant)
        # Nitrogen fertilization
        n_amount = self.fert_amount * action
        self.model._send_signal(signal=pcse.signals.apply_npk, \
                                    N_amount=n_amount, N_recovery=self.n_recovery)

        return (n_amount, 0, 0, 0)

# Simulating production under limited water and Nitrogen
class Limited_NW_Env(NPK_Env):
    config = utils.make_config()
    config['SOIL'] = SoilModuleWrapper_LNW
    config['CROP'] = Wofost80
    config['AGROMANAGEMENT'] = AgroManagerSingleYear
    def __init__(self, args):
        super().__init__(args)
        self.action_space = gym.spaces.Discrete(self.num_fert + self.num_irrig)

    def _take_action(self, action):
        n_amount = 0
        irrig_amount = 0

        # Irrigation action
        if action >= self.num_fert:
            irrig_amount -= self.num_fert
            self.model._send_signal(signal=pcse.signals.irrigate, amount=irrig_amount, \
                                    efficiency=self.irrig_effec)

        # Fertilizaiton action, correct for 2 crop specific actions (harvest/plant)
        # Nitrogen fertilization
        else:
            n_amount = self.fert_amount * action
            self.model._send_signal(signal=pcse.signals.apply_npk, \
                                    N_amount=n_amount, N_recovery=self.n_recovery)

        return (n_amount, 0, 0, irrig_amount)


# Simulating production under limited water 
class Limited_W_Env(NPK_Env):
    config = utils.make_config()
    config['SOIL'] = SoilModuleWrapper_LW
    config['CROP'] = Wofost80
    config['AGROMANAGEMENT'] = AgroManagerSingleYear
    def __init__(self, args):
        super().__init__(args)

        self.action_space = gym.spaces.Discrete(self.num_irrig)

    def _take_action(self, action):

        irrig_amount = action
        self.model._send_signal(signal=pcse.signals.irrigate, amount=irrig_amount, \
                                efficiency=self.irrig_effec)

        return (0, 0, 0, irrig_amount)