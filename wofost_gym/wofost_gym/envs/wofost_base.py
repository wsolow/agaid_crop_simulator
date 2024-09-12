"""Main API for the WOFOST Gym environment. All other environments inherit
from the NPK_Env Gym Environment"""

import os
import datetime
from datetime import date
import numpy as np
import pandas as pd
import yaml

import gymnasium as gym
import pcse
from pcse.engine import Wofost8Engine

from wofost_gym.args import NPK_Args
from wofost_gym import exceptions as exc
from wofost_gym import utils
from pcse import NASAPowerWeatherDataProvider


class NPK_Env(gym.Env):
    """Base Gym Environment for simulating crop growth
    
    Relies on the PCSE package (in base folder) and the WOFOST80 crop model. 
    """

    # Env Constants
    NUM_ACT = 4
    N = 0 # Nitrogen action
    P = 1 # Phosphorous action
    K = 2 # Potassium action
    I = 3 # Irrigation action 

    WEATHER_YEARS = [1984, 2023]
    MISSING_YEARS = []

    def __init__(self, args: NPK_Args, config:dict=None):
        """Initialize the :class:`NPK_Env`.

        Args: 
            NPK_Args: The environment parameterization
            config: Agromanagement configuration dictionary
        """
        # Arguments
        self.config=config
        self.seed(args.seed)
        self.args = args
        self.wofost_params = args.wf_args
        self.agro_params = args.ag_args

        # Forecasting and action frequency
        self.intervention_interval = args.intvn_interval
        self.forecast_length = args.forecast_length
        self.forecast_noise = args.forecast_noise
        self.random_reset = args.random_reset

        # Get the weather and output variables
        self.weather_vars = args.weather_vars
        self.output_vars = args.output_vars

        # Check that the configuration is valid
        self._validate()

        self.log = self._init_log()
       
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

        self.weatherdataprovider = NASAPowerWeatherDataProvider(*self.location)
        self.train_weather_data = self._get_train_weather_data()
        
        # Override parameters - must happen before initiaziing crop engine
        utils.set_params(self, self.wofost_params)
        
        # Initialize crop engine
        self.model = Wofost8Engine(self.parameterprovider, self.weatherdataprovider,
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

        # Create action and observation spaces
        self.action_space = gym.spaces.Discrete(1+3*self.num_fert + self.num_irrig)
        self.observation_space = gym.spaces.Box(low=-np.inf, high=np.inf, \
                                shape=(1+len(self.output_vars)+len(self.weather_vars)*self.forecast_length,))

    def seed(self, seed: int=None):
        """Set the seed for the environment using Gym seeding.
        Minimal impact - generally will only effect Gaussian noise for 
        weather predictions
        
        Args:
            seed: int - seed for the environment"""
        self.np_random_seed, seed = gym.utils.seeding.np_random(seed)
        return [seed]
        
    def render(self, mode: str='human', close: bool=False):
        """Render the environment into something a human can understand"""
        msg = "Render not implemented for Ag Environment"
        raise NotImplementedError(msg)
    
    def reset(self, **kwargs):
        """Reset the environment to the initial state specified by the 
        agromanagement, crop, and soil files.
        
        Args:
            **kwargs:
                year: year to reset enviroment to for weather
                location: (latitude, longitude). Location to set environment to"""
        self.log = self._init_log()

        if 'year' in kwargs:
            self.year = kwargs['year']
            if self.year <= self.WEATHER_YEARS[0] or self.year >= self.WEATHER_YEARS[1]+1 \
                or self.year in self.MISSING_YEARS:
                msg = f"Specified year {self.year} outside of range {self.WEATHER_YEARS}"
                raise exc.ResetException(msg) 

        if 'location' in kwargs:
            self.location = kwargs['location']
            if self.location[0] <= -90 or self.location >= 90:
                msg = f"Latitude {self.location[0]} outside of range (-90, 90)"
                raise exc.ResetException(msg)
            
            if self.location[1] <= -180 or self.location >= 180:
                msg = f"Longitude {self.location[0]} outside of range (-180, 180)"
                raise exc.ResetException(msg)

        # Reset to random year if random-reset. Useful for RL algorithms 
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

        # Update agromanagement dictionary
        self.agromanagement['CropCalendar']['crop_start_date'] = self.crop_start_date
        self.agromanagement['CropCalendar']['crop_end_date'] = self.crop_end_date
        self.agromanagement['SiteCalendar']['site_start_date'] = self.site_start_date
        self.agromanagement['SiteCalendar']['site_end_date'] = self.site_end_date
    
        # Reset weather 
        self.weatherdataprovider = NASAPowerWeatherDataProvider(*self.location)

        # Override parameters
        utils.set_params(self, self.wofost_params)

        # Reset model
        self.model = Wofost8Engine(self.parameterprovider, self.weatherdataprovider,
                                         self.agromanagement, config=self.config)
        
        # Generate initial output
        output = self._run_simulation()
        observation = self._process_output(output)

        return observation, self.log

    def step(self, action):
        """Run one timestep of the environment's dynamics.

        Sends action to the WOFOST model and recieves the resulting observation
        which is then processed to the _get_reward() function and _process_output()
        function for a reward and observation

        Args:
            action: integer
        """

        if action < 0 or action >= self.action_space.n:
            msg = f"Action {action} outside of range [0, {self.action_space.n}]"
            raise exc.ActionException(msg)
        
        # Send action signal to model and run model
        act_tuple = self._take_action(action)
        output = self._run_simulation()

        observation = self._process_output(output)
        
        reward = self._get_reward(output, action) 
        
        # Terminate based on site end date
        terminate = self.date >= self.site_end_date
        # Truncate (in some cases) based on the crop end date
        truncation = self.date >= self.crop_end_date

        self._log(output.iloc[-1]['WSO'], act_tuple, reward)

        #TODO Truncations and crop signals
        truncation = False

        return observation, reward, terminate, truncation, self.log
    
    def _validate(self):
        """Validate that the configuration is correct """
        if self.config is None:
            msg = "Configuration Not Specified. Please use model"
            raise exc.WOFOSTGymError(msg)
        
        # Check that WSO is present
        if 'WSO' not in self.output_vars:
            msg = 'Crop State \'WSO\' variable must be in output variables'
            raise exc.WOFOSTGymError(msg)
        
    def _load_agromanagement_data(self, path: str):
        """Load the Agromanagement .yaml file
        
        Args:
            path: filepath string to agromanagement file
         """
        with open(os.path.join(path)) as file:
            agromanagement = yaml.load(file, Loader=yaml.SafeLoader)
        if "AgroManagement" in agromanagement:
            agromanagement = agromanagement["AgroManagement"]
        
        return utils.set_agro_params(agromanagement, self.agro_params)
    
    def _load_site_parameters(self, agromanagement: dict):
        """Load the site parameters from the agromanagement file. This is the
            SiteCalendar portion of the .yaml file

        Args:
            agromanagement: dictionary - see /env_config/README for information
        """
        try: 
            site_params = agromanagement['SiteCalendar']
            
            fixed_location = (site_params['latitude'], site_params['longitude'])
            fixed_year = site_params['year']
        except:
            msg = "Missing \'latitude\', \'longitude\' or \'year\' keys missing from config file"
            raise exc.ConfigFileException(msg)
        
        return fixed_location, fixed_year
    
    def _get_train_weather_data(self, year_range: list=WEATHER_YEARS, \
                                missing_years: list=MISSING_YEARS):
        """Return the valid years of historical weather data for use in the 
        NASA Weather Provider.

        Generally do not need to specify these arguments, but some locations may
        not have the requisite data for that year.
        
        Args: 
            year_range: list of [low, high]
            missing_years: list of years that have missing data
        """
        return [year for year in np.arange(year_range[0], year_range[1]+1) if year not in missing_years]
    
    def _get_weather(self, date:date):
        """Get the weather for a range of days from the NASA Weather Provider.

        Handles weather forecasting by adding some amount of pre-specified Gaussian
        noise to the forecast. Increasing in strength as the forecast horizon
        increases.
        
        Args:
            date: datetime - day to start collecting the weather information
        """
        weather_vars = []
        noise_scale = np.linspace(start=self.forecast_noise[0], \
                                  stop=self.forecast_noise[1], num=self.forecast_length)
        
        # For every day in the forecasting window
        for i in range(0, self.forecast_length):
            weather = self._get_weather_day(date + datetime.timedelta(i) )

            # Add random noise to weather prediction
            weather += np.random.normal(size=len(weather)) * weather * noise_scale[i] 
            weather_vars.append(weather)

        return np.array(weather_vars)

    def _get_weather_day(self, date: date):
        """Get the weather for a specific date based on the desired weather
        variables
        
        Args:
            date: datetime - day which to get weather information
        """
        weatherdatacontainer = self.weatherdataprovider(date)

        return [getattr(weatherdatacontainer, attr) for attr in self.weather_vars]
    
    def _process_output(self, output: dict):
        """Process the output from the model into the observation required by
        the current environment
        
        Args:
            output: dictionary of model output variables
        """

        # Current day crop observation
        crop_observation = np.array(output.iloc[-1][self.output_vars])
        self.date = output.index[-1]

        # Observed weather through the specified forecast
        weather_observation = self._get_weather(self.date)

        # Count the number of days elapsed - for time-based policies
        days_elapsed = self.date - self.site_start_date

        observation = np.concatenate([crop_observation, weather_observation.flatten(), [days_elapsed.days]])

        return observation.astype('float32')

    def _run_simulation(self):
        """Run the WOFOST model for the specified number of days
        """
        self.model.run(days=self.intervention_interval)
        output = pd.DataFrame(self.model.get_output()).set_index("day")

        # Fill missing values with nans - arises when crop has not been
        # planted yet. 
        with pd.option_context("future.no_silent_downcasting", True):
            output = output.fillna(value=np.nan).infer_objects(copy=False)
        return output

    def _take_action(self, action: int):
        """Controls sending fertilization and irrigation signals to the model. 

        Converts the integer action to a signal and amount of NPK/Water to be applied.
        
        Args:
            action
        """
        msg = "\'Take Action\' method not yet implemented on %s" % self.__class__.__name__
        raise NotImplementedError(msg)

    def _get_reward(self, output: dict, act_tuple: tuple):
        """Convert the reward by applying a high penalty if a fertilization
        threshold is crossed
        
        Args:
            output     - of the simulator
            act_tuple  - amount of NPK/Water applied
        """
        return np.nan_to_num(output.iloc[-1]['WSO'])
        
    def _init_log(self):
        """Initialize the log.
        """
        
        return {'growth': dict(), 'nitrogen': dict(), 'phosphorous': dict(), 'potassium': dict(), 'irrigation':dict(), 'reward': dict(), 'day':dict()}
    
    def _log(self, growth: float, action: int, reward: float):
        """Log the outputs into the log dictionary
        
        Args: 
            growth: float - Weight of Storage Organs
            action: int   - the action taken by the agent
            reward: float - the reward
        """

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

class Harvest_NPK_Env(NPK_Env):
    """Base Gym Environment for simulating crop growth with planting and 
    harvesting actions. Does not automatically start crop
    
    Relies on the PCSE package (in base folder) and the WOFOST80 crop model. 
    """
    # Env Constants
    NUM_ACT = 6
    P = 0 # Plant action
    H = 1 # Harvest action
    N = 2 # Nitrogen action
    P = 3 # Phosphorous action
    K = 4 # Potassium action
    I = 5 # Irrigation action 

    def __init__(self, args: NPK_Args, config: dict=None):
        """Initialize the :class:`Harvest_NPK_Env`.

        Args: 
            NPK_Args: The environment parameterization
            config: Agromanagement configuration dictionary
        """
        super().__init__(args, config)

        # Get specific crop names from agromanagement
        self.crop_name = self.agromanagement['CropCalendar']['crop_name']
        self.variety_name = self.agromanagement['CropCalendar']['variety_name']
        self.crop_start_type = self.agromanagement['CropCalendar']['crop_start_type']
        self.crop_end_type = self.agromanagement['CropCalendar']['crop_end_type']
        self.active_crop_flag = False

    def _take_action(self, action: int):
        """Sends action to the model
        """
        msg = "\'Take Action\' method not yet implemented on %s" % self.__class__.__name__
        raise NotImplementedError(msg)

    def _init_log(self):
        """Initialize the log.
        """
        return {'growth': dict(), 'plant': dict(), 'harvest': dict(), 'nitrogen': dict(), \
                'phosphorous': dict(), 'potassium': dict(), 'irrigation':dict(), 'reward': dict(), 'day':dict()}
    
    def _log(self, growth: float, action: int, reward: float):
        """Log the outputs into the log dictionary
        
        Args: 
            growth: float - Weight of Storage Organs
            action: int   - the action taken by the agent
            reward: float - the reward
        """
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
