import os
import datetime
import numpy as np
import pandas as pd
import yaml

import gymnasium as gym
import pcse
from pathlib import Path

# Action Enums
N_ACT = 0
P_ACT = 1
K_ACT = 2
W_ACT = 3

# Base model simulating growth of crop subject to NPK and water limited dynamics
class NPK_Env(gym.Env):

    def __init__(self, args):
        self.seed(args.seed)
        self.log = self._init_log()

        self.intervention_interval = args.intvn_interval
        self.random_reset = args.random_reset

        # Get the weather and output variables
        self.weather_vars = args.weather_vars
        self.output_vars = args.output_vars
       
        # Load all model parameters from .yaml files
        crop = pcse.fileinput.YAMLCropDataProvider(fpath=os.path.join(args.path, args.crop_fpath))
        site = pcse.fileinput.YAMLSiteDataProvider(fpath=os.path.join(args.path, args.site_fpath))

        self.parameterprovider = pcse.base.ParameterProvider(sitedata=site, cropdata=crop)
        self.agromanagement = self._load_agromanagement_data(os.path.join(args.path, args.agro_fpath))
        self.fixed_location, self.fixed_year = self._load_site_parameters(self.agromanagement)
        self.crop_start_date = self.agromanagement[0][next(iter(self.agromanagement[0].keys()))]['CropCalendar']['crop_start_date']
        self.crop_start_date = self.agromanagement[0][next(iter(self.agromanagement[0].keys()))]['CropCalendar']['crop_end_date']
        

        self.weatherdataprovider = self._get_weatherdataprovider()
        self.train_weather_data = self._get_train_weather_data()
        
        # Create crop model
        self.model = pcse.models.Wofost80_NWLP_FD_beta(self.parameterprovider, self.weatherdataprovider,
                                         self.agromanagement)
        self.date = self.crop_start_date

        # NPK/Irrigation action amounts
        self.num_n = args.num_fert
        self.num_p = args.num_fert
        self.num_k = args.num_fert
        self.num_irrig = args.num_irrig
        self.num_actions = np.max([self.num_n, self.num_p, self.num_k, self.num_irrig])

        self.fert_amount = args.fert_amount
        self.irrig_amount = args.irrig_amount
        self.n_recovery = args.n_recovery
        self.p_recovery = args.p_recovery
        self.k_recovery = args.k_recovery

        # Penalty term for fertilization cost
        self.beta = args.beta

        # Create action and observation spaces
        self.action_space = gym.spaces.MultiDiscrete(nvec=[4, self.num_actions], dtype=int)
        self.observation_space = gym.spaces.Box(low=-np.inf, high=np.inf, \
                                shape=(len(self.output_vars)+len(self.weather_vars)*args.intvn_interval,))
   
    # Load the agromanagement file 
    def _load_agromanagement_data(self, path):
        with open(os.path.join(path)) as file:
            agromanagement = yaml.load(file, Loader=yaml.SafeLoader)
        return agromanagement
    
    # Load the site parameters from agromanagement file
    def _load_site_parameters(self, agromanagement):
        try: 
            site_params = agromanagement[0][next(iter(agromanagement[0].keys()))]['Site']
            
            fixed_location = (site_params['LATITUDE'], site_params['LONGITUDE'])
            fixed_year = site_params['YEAR']
        except:
            fixed_location = None
            fixed_year = None
        return fixed_location, fixed_year
    
    # Get the historical weather based on the location and year
    def _get_weatherdataprovider(self):
        location = self.fixed_location
        if self.fixed_location is None:
            latitude = self.np_random.choice([51.5, 52, 52.5])
            longitude = self.np_random.choice([5, 5.5, 6])
            location = (latitude, longitude)
        return pcse.db.NASAPowerWeatherDataProvider(*location)
    
    # Get the training weather data
    def _get_train_weather_data(self):
        all_years = range(1984, 2018)
        missing_data = []
        train_weather_data = [year for year in all_years if year not in missing_data]
        return train_weather_data
    
    # Get the weather for a range of days
    def _get_weather(self, weatherdataprovider, date, days):
        dates = [date + datetime.timedelta(i) for i in range(0, days)]
        weather = [self._get_weather_day(weatherdataprovider, day) for day in dates]
        return np.array(weather)

    # Get the weather for specific date
    def _get_weather_day(self, weatherdataprovider, date):
        weatherdatacontainer = weatherdataprovider(date)
        weather = [getattr(weatherdatacontainer, attr) for attr in self.weather_vars]
        return weather
    
    # Set the year to the year specified in the agromanagement file
    def _random_year(self):
        dict_ = self.agromanagement[0]
        old_date = next(iter(dict_.keys()))

        target_year = self.np_random.choice(self.train_weather_data) 
        
        new_date = old_date.replace(target_year)
        content = dict_[old_date]
        crop_start_date = content['CropCalendar']['crop_start_date'].replace(target_year)
        content['CropCalendar']['crop_start_date'] = crop_start_date
        crop_end_date = content['CropCalendar']['crop_end_date'].replace(target_year)
        content['CropCalendar']['crop_end_date'] = crop_end_date
        dict_[new_date] = dict_.pop(old_date)
        return crop_start_date, crop_end_date
    
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

        # Reset to random year if flag
        if self.random_reset:
            self.crop_start_date, self.crop_end_date = self._random_year()
        else:
            self.crop_start_date = \
                list(self.agromanagement[0].values())[0]['CropCalendar']['crop_start_date']
            self.crop_end_date = \
                list(self.agromanagement[0].values())[0]['CropCalendar']['crop_end_date']
        
        self.date = self.crop_start_date
        # Reset weather 
        self.weatherdataprovider = self._get_weatherdataprovider()
        # Reset model
        self.model = pcse.models.Wofost80_NWLP_FD_beta(self.parameterprovider, self.weatherdataprovider,
                                         self.agromanagement)
        
        # Generate first part of output 
        output = self._run_simulation(self.model)
        observation = self._process_output(output)

        return observation, self.log

    # Step through the environment
    def step(self, action):
        npk, irrigation = self._take_action(action)
        output = self._run_simulation(self.model)

        observation = self._process_output(output)
        self.date = output.index[-1]
        reward = self._get_reward(output, action) 
        done = self.date >= self.crop_end_date

        self._log(output.iloc[-1]['WSO'], npk, irrigation, reward)

        #TODO Truncations and crop signals
        truncation = False

        return observation, reward, done, truncation, self.log
    
    # Concatenate crop and weather observations
    def _process_output(self, output):
        # Current crop observation
        crop_observation = np.array(output.iloc[-1][self.output_vars])

        # Observed weather until next intervention time
        weather_observation = self._get_weather(self.weatherdataprovider, self.date,
                                             self.intervention_interval)
        
        observation = np.concatenate([crop_observation, weather_observation.flatten()])
        observation = np.nan_to_num(observation)

        return observation.astype('float32')

    # Run a step in the model
    def _run_simulation(self, model):
        model.run(days=self.intervention_interval)
        output = pd.DataFrame(model.get_output()).set_index("day")

        # Gets rid of deprecation warning on fillna
        with pd.option_context("future.no_silent_downcasting", True):
            output = output.fillna(value=np.nan).infer_objects(copy=False)
        return output

    # Send action to the model
    def _take_action(self, action):
        n_amount = self.fert_amount * action[1] * (action[0] == N_ACT)
        p_amount = self.fert_amount * action[1] * (action[0] == P_ACT)
        k_amount = self.fert_amount * action[1] * (action[0] == K_ACT)
        irrig_amount = self.irrig_amount * action[1] * (action[0] == W_ACT)

        self.model._send_signal(signal=pcse.signals.apply_npk, N_amount=n_amount, \
                                P_amount=p_amount, K_amount=k_amount, N_recovery=self.n_recovery,\
                                P_recovery=self.p_recovery, K_recovery=self.k_recovery)
        
        self.model._send_signal(signal=pcse.signals.irrigate, amount=irrig_amount, efficiency=0.7)
        return (n_amount, p_amount, k_amount), irrig_amount

    # Get reward from the simulation
    def _get_reward(self, output, action):
        n_amount = self.fert_amount * action[1] * (action[0] == N_ACT)
        p_amount = self.fert_amount * action[1] * (action[0] == P_ACT)
        k_amount = self.fert_amount * action[1] * (action[0] == K_ACT)
        irrig_amount = self.irrig_amount * action[1] * (action[0] == W_ACT)
        reward = output.iloc[-1]['WSO'] - \
                        (np.sum(self.beta * np.array([n_amount, p_amount, k_amount])) \
                        - .25 * self.beta * irrig_amount)
        return reward
        
    def _init_log(self):
        return {'growth': dict(), 'nitrogen': dict(), 'phosphorous': dict(), 'potassium': dict(), 'irrigation':dict(), 'reward': dict(), 'day':dict()}
    
    def _log(self, growth, npk, irrigation, reward):
        self.log['growth'][self.date] = growth
        self.log['nitrogen'][self.date - datetime.timedelta(self.intervention_interval)] = \
            npk[0]
        self.log['phosphorous'][self.date - datetime.timedelta(self.intervention_interval)] = \
            npk[1]
        self.log['potassium'][self.date - datetime.timedelta(self.intervention_interval)] = \
            npk[2]
        self.log['irrigation'][self.date - datetime.timedelta(self.intervention_interval)] = \
            irrigation
        self.log['reward'][self.date] = reward
        self.log['day'][self.date] = self.date  

# Simulating Potential Production - useful for seeing how much the crop
# could grow without water limiting conditions
# Note that given how the WaterBalance (WC) and Soil Moisture (SM) are computed
# The graph of their values will look abnormal, however this still allows for 
# Excess water to be available in the soil 
class PP_Env(NPK_Env):
    def __init__(self, args):
        super().__init__(args)

    # Inherits same reset function, except for manually holding npk and water 
    # level values at maximum
    def reset(self, **kwargs):
        self.log = self._init_log()

        # Reset to random year if flag
        if self.random_reset:
            self.crop_start_date, self.crop_end_date = self._random_year()
        else:
            self.crop_start_date = \
                list(self.agromanagement[0].values())[0]['CropCalendar']['crop_start_date']
            self.crop_end_date = \
                list(self.agromanagement[0].values())[0]['CropCalendar']['crop_end_date']
        
        self.date = self.crop_start_date
        # Reset weather 
        self.weatherdataprovider = self._get_weatherdataprovider()
        # Reset model
        self.model = pcse.models.Wofost80_NWLP_FD_beta(self.parameterprovider, self.weatherdataprovider,
                                         self.agromanagement)
        
        self.model.soil.WaterbalanceFD.states.WC =  100.
        self.model.soil.NPK_Soil_Dynamics.states.NAVAIL = 100.
        self.model.soil.NPK_Soil_Dynamics.states.PAVAIL = 100.
        self.model.soil.NPK_Soil_Dynamics.states.KAVAIL = 100.
        
        # Generate first part of output 
        output = self._run_simulation(self.model)
        observation = self._process_output(output)


        return observation, self.log

    # Step through the environment
    def step(self, action):
        # Manually set soil values to maximum
        self.model.soil.WaterbalanceFD.states.WC = 100. 
        self.model.soil.NPK_Soil_Dynamics.states.NAVAIL = 100.
        self.model.soil.NPK_Soil_Dynamics.states.PAVAIL = 100.
        self.model.soil.NPK_Soil_Dynamics.states.KAVAIL = 100.

        npk, irrigation = self._take_action(action)
        output = self._run_simulation(self.model)

        observation = self._process_output(output)
        self.date = output.index[-1]
        reward = self._get_reward(output, action) 
        done = self.date >= self.crop_end_date

        self._log(output.iloc[-1]['WSO'], npk, irrigation, reward)

        #TODO Truncations and crop signals
        truncation = False

        return observation, reward, done, truncation, self.log

# Simulating production under abundant water but limited NPK dynamics
class Limited_NPK_Env(NPK_Env):

    def __init__(self, args):
        super().__init__(args)

    # Inherits same reset function, except for manually holding npk and water 
    # level values at maximum
    def reset(self, **kwargs):
        self.log = self._init_log()

        # Reset to random year if flag
        if self.random_reset:
            self.crop_start_date, self.crop_end_date = self._random_year()
        else:
            self.crop_start_date = \
                list(self.agromanagement[0].values())[0]['CropCalendar']['crop_start_date']
            self.crop_end_date = \
                list(self.agromanagement[0].values())[0]['CropCalendar']['crop_end_date']
        
        self.date = self.crop_start_date
        # Reset weather 
        self.weatherdataprovider = self._get_weatherdataprovider()
        # Reset model
        self.model = pcse.models.Wofost80_NWLP_FD_beta(self.parameterprovider, self.weatherdataprovider,
                                         self.agromanagement)
        
        self.model.soil.WaterbalanceFD.states.WC =  100.
        
        # Generate first part of output 
        output = self._run_simulation(self.model)
        observation = self._process_output(output)


        return observation, self.log

    # Step through the environment
    def step(self, action):
        # Manually set soil values to maximum
        self.model.soil.WaterbalanceFD.states.WC = 100. 

        npk, irrigation = self._take_action(action)
        output = self._run_simulation(self.model)

        observation = self._process_output(output)
        self.date = output.index[-1]
        reward = self._get_reward(output, action) 
        done = self.date >= self.crop_end_date

        self._log(output.iloc[-1]['WSO'], npk, irrigation, reward)

        #TODO Truncations and crop signals
        truncation = False

        return observation, reward, done, truncation, self.log
    
# Simulating production under limited Nitrogen but abundant water and P/K
class Limited_N_Env(NPK_Env):

    def __init__(self, args):
        super().__init__(args)

    # Inherits same reset function, except for manually holding npk and water 
    # level values at maximum
    def reset(self, **kwargs):
        self.log = self._init_log()

        # Reset to random year if flag
        if self.random_reset:
            self.crop_start_date, self.crop_end_date = self._random_year()
        else:
            self.crop_start_date = \
                list(self.agromanagement[0].values())[0]['CropCalendar']['crop_start_date']
            self.crop_end_date = \
                list(self.agromanagement[0].values())[0]['CropCalendar']['crop_end_date']
        
        self.date = self.crop_start_date
        # Reset weather 
        self.weatherdataprovider = self._get_weatherdataprovider()
        # Reset model
        self.model = pcse.models.Wofost80_NWLP_FD_beta(self.parameterprovider, self.weatherdataprovider,
                                         self.agromanagement)
        
        self.model.soil.WaterbalanceFD.states.WC =  100.
        self.model.soil.NPK_Soil_Dynamics.states.PAVAIL = 100.
        self.model.soil.NPK_Soil_Dynamics.states.KAVAIL = 100.
        
        # Generate first part of output 
        output = self._run_simulation(self.model)
        observation = self._process_output(output)


        return observation, self.log

    # Step through the environment
    def step(self, action):
        # Manually set soil values to maximum
        self.model.soil.WaterbalanceFD.states.WC = 100. 
        self.model.soil.NPK_Soil_Dynamics.states.PAVAIL = 100.
        self.model.soil.NPK_Soil_Dynamics.states.KAVAIL = 100.

        npk, irrigation = self._take_action(action)
        output = self._run_simulation(self.model)

        observation = self._process_output(output)
        self.date = output.index[-1]
        reward = self._get_reward(output, action) 
        done = self.date >= self.crop_end_date

        self._log(output.iloc[-1]['WSO'], npk, irrigation, reward)

        #TODO Truncations and crop signals
        truncation = False

        return observation, reward, done, truncation, self.log
    
# Simulating production under limited water and Nitrogen
class Limited_NW_Env(NPK_Env):

    def __init__(self, args):
        super().__init__(args)

    # Inherits same reset function, except for manually holding npk and water 
    # level values at maximum
    def reset(self, **kwargs):
        self.log = self._init_log()

        # Reset to random year if flag
        if self.random_reset:
            self.crop_start_date, self.crop_end_date = self._random_year()
        else:
            self.crop_start_date = \
                list(self.agromanagement[0].values())[0]['CropCalendar']['crop_start_date']
            self.crop_end_date = \
                list(self.agromanagement[0].values())[0]['CropCalendar']['crop_end_date']
        
        self.date = self.crop_start_date
        # Reset weather 
        self.weatherdataprovider = self._get_weatherdataprovider()
        # Reset model
        self.model = pcse.models.Wofost80_NWLP_FD_beta(self.parameterprovider, self.weatherdataprovider,
                                         self.agromanagement)
        
        self.model.soil.NPK_Soil_Dynamics.states.PAVAIL = 100.
        self.model.soil.NPK_Soil_Dynamics.states.KAVAIL = 100.
        
        # Generate first part of output 
        output = self._run_simulation(self.model)
        observation = self._process_output(output)


        return observation, self.log

    # Step through the environment
    def step(self, action):
        # Manually set soil values to maximum
        self.model.soil.NPK_Soil_Dynamics.states.PAVAIL = 100.
        self.model.soil.NPK_Soil_Dynamics.states.KAVAIL = 100.

        npk, irrigation = self._take_action(action)
        output = self._run_simulation(self.model)

        observation = self._process_output(output)
        self.date = output.index[-1]
        reward = self._get_reward(output, action) 
        done = self.date >= self.crop_end_date

        self._log(output.iloc[-1]['WSO'], npk, irrigation, reward)

        #TODO Truncations and crop signals
        truncation = False

        return observation, reward, done, truncation, self.log

# Simulating production under limited water 
class Limited_W_Env(NPK_Env):
    def __init__(self, args):
        super().__init__(args)

    # Inherits same reset function, except for manually holding npk and water 
    # level values at maximum
    def reset(self, **kwargs):
        self.log = self._init_log()

        # Reset to random year if flag
        if self.random_reset:
            self.crop_start_date, self.crop_end_date = self._random_year()
        else:
            self.crop_start_date = \
                list(self.agromanagement[0].values())[0]['CropCalendar']['crop_start_date']
            self.crop_end_date = \
                list(self.agromanagement[0].values())[0]['CropCalendar']['crop_end_date']
        
        self.date = self.crop_start_date
        # Reset weather 
        self.weatherdataprovider = self._get_weatherdataprovider()
        # Reset model
        self.model = pcse.models.Wofost80_NWLP_FD_beta(self.parameterprovider, self.weatherdataprovider,
                                         self.agromanagement)
        
        self.model.soil.NPK_Soil_Dynamics.states.NAVAIL = 100.
        self.model.soil.NPK_Soil_Dynamics.states.PAVAIL = 100.
        self.model.soil.NPK_Soil_Dynamics.states.KAVAIL = 100.
        
        # Generate first part of output 
        output = self._run_simulation(self.model)
        observation = self._process_output(output)


        return observation, self.log

    # Step through the environment
    def step(self, action):
        # Manually set soil values to maximum
        self.model.soil.NPK_Soil_Dynamics.states.NAVAIL = 100.
        self.model.soil.NPK_Soil_Dynamics.states.PAVAIL = 100.
        self.model.soil.NPK_Soil_Dynamics.states.KAVAIL = 100.

        npk, irrigation = self._take_action(action)
        output = self._run_simulation(self.model)

        observation = self._process_output(output)
        self.date = output.index[-1]
        reward = self._get_reward(output, action) 
        done = self.date >= self.crop_end_date

        self._log(output.iloc[-1]['WSO'], npk, irrigation, reward)

        #TODO Truncations and crop signals
        truncation = False

        return observation, reward, done, truncation, self.log
 