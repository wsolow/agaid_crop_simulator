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
    config = "Wofost80.conf"
    def __init__(self, args):
        self.seed(args.seed)
        self.log = self._init_log()
        self.args = args
        self.wofost_params = args.wf_args

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
        self.location, self.year = self._load_site_parameters(self.agromanagement)
        self.crop_start_date = self.agromanagement[0][next(iter(self.agromanagement[0].keys()))]['CropCalendar']['crop_start_date']
        self.crop_start_date = self.agromanagement[0][next(iter(self.agromanagement[0].keys()))]['CropCalendar']['crop_end_date']
        self.campaign_start = list(self.agromanagement[0].keys())[0]        

        self.weatherdataprovider = self._get_weatherdataprovider()
        self.train_weather_data = self._get_train_weather_data()
        
        # Override parameters
        self._set_params(self.wofost_params)
        
        # Create crop model
        self.model = pcse.models.Wofost80(self.parameterprovider, self.weatherdataprovider,
                                         self.agromanagement, config=self.config)
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

        # Thresholds for nutrient application
        self.max_n = args.max_n
        self.max_p = args.max_p
        self.max_k = args.max_k
        self.max_w = args.max_w

        # Penalty term for fertilization cost
        self.beta = args.beta

        # Create action and observation spaces
        self.action_space = gym.spaces.MultiDiscrete(nvec=[4, self.num_actions], dtype=int)
        self.observation_space = gym.spaces.Box(low=-np.inf, high=np.inf, \
                                shape=(1+len(self.output_vars)+len(self.weather_vars)*args.intvn_interval,))

    def _set_params(self, args):
            # All editable parameters for the WOFOST crop and soil. If left to default
        # of None, values will be drawn from the .yaml files in /env_config/
        # NPK Soil dynamics params
        """Base soil supply of N available through mineralization kg/ha"""
        if args.NSOILBASE is not None:
            self.parameterprovider.set_override("NSOILBASE", args.NSOILBASE, check=False)  
        """Fraction of base soil N that comes available every day"""    
        if args.NSOILBASE_FR is not None:     
            self.parameterprovider.set_override("NSOILBASE_FR", args.NSOILBASE_FR, check=False)  
        """Base soil supply of P available through mineralization kg/ha"""
        if args.PSOILBASE is not None:
            self.parameterprovider.set_override("PSOILBASE", args.PSOILBASE, check=False)
        """Fraction of base soil P that comes available every day"""         
        if args.PSOILBASE_FR is not None:
            self.parameterprovider.set_override("PSOILBASE_FR", args.PSOILBASE_FR, check=False)
        """Base soil supply of K available through mineralization kg/ha"""
        if args.KSOILBASE is not None:
            self.parameterprovider.set_override("KSOILBASE", args.KSOILBASE, check=False)
        """Fraction of base soil K that comes available every day""" 
        if args.KSOILBASE_FR is not None:        
            self.parameterprovider.set_override("KSOILBASE_FR", args.KSOILBASE_FR, check=False)
        """Initial N available in the N pool (kg/ha)"""
        if args.NAVAILI is not None:
            self.parameterprovider.set_override("NAVAILI", args.NAVAILI, check=False)
        """Initial P available in the P pool (kg/ha)"""
        if args.PAVAILI is not None:
            self.parameterprovider.set_override("PAVAILI", args.PAVAILI, check=False)
        """Initial K available in the K pool (kg/ha)"""
        if args.KAVAILI is not None:
            self.parameterprovider.set_override("KAVAILI", args.KAVAILI, check=False)
        """Background supply of N through atmospheric deposition (kg/ha/day)"""
        if args.BG_N_SUPPLY is not None:
            self.parameterprovider.set_override("BG_N_SUPPLY", args.BG_N_SUPPLY, check=False)
        """Background supply of P through atmospheric deposition (kg/ha/day)"""
        if args.BG_P_SUPPLY is not None:
            self.parameterprovider.set_override("BG_P_SUPPLY", args.BG_P_SUPPLY, check=False)
        """Background supply of K through atmospheric deposition (kg/ha/day)"""
        if args.BG_K_SUPPLY is not None:
            self.parameterprovider.set_override("BG_K_SUPPLY", args.BG_K_SUPPLY, check=False)

        # Waterbalance soil dynamics params
        """Field capacity of the soil"""
        if args.SMFCF is not None:
            self.parameterprovider.set_override("SMFCF", args.SMFCF, check=False)             
        """Porosity of the soil"""
        if args.SM0 is not None:
            self.parameterprovider.set_override("SM0", args.SM0, check=False)                            
        """Wilting point of the soil"""
        if args.SMW is not None:    
            self.parameterprovider.set_override("SMW", args.SMW, check=False)                  
        """Soil critical air content (waterlogging)"""
        if args.CRAIRC is not None:
            self.parameterprovider.set_override("CRAIRC", args.CRAIRC, check=False)
        """maximum percolation rate root zone (cm/day)"""
        if args.SOPE is not None:
            self.parameterprovider.set_override("SOPE", args.SOPE, check=False)
        """maximum percolation rate subsoil (cm/day)"""
        if args.KSUB is not None:
            self.parameterprovider.set_override("KSUB", args.KSUB, check=False)
        """Soil rootable depth (cm)"""
        if args.RDMSOL is not None:
            self.parameterprovider.set_override("RDMSOL", args.RDMSOL, check=False)                     
        """Indicates whether non-infiltrating fraction of rain is a function of storm size (1) or not (0)"""
        if args.IFUNRN is not None:
            self.parameterprovider.set_override("IFUNRN", args.IFUNRN, check=False)
        """Maximum surface storage (cm)"""                               
        if args.SSMAX is not None:
            self.parameterprovider.set_override("SSMAX", args.SSMAX, check=False)               
        """Initial surface storage (cm)"""
        if args.SSI is not None:
            self.parameterprovider.set_override("SSI", args.SSI, check=False)   
        """Initial amount of water in total soil profile (cm)"""
        if args.WAV is not None:
            self.parameterprovider.set_override("WAV", args.WAV, check=False)
        """Maximum fraction of rain not-infiltrating into the soil"""
        if args.NOTINF is not None:   
            self.parameterprovider.set_override("NOTINF", args.NOTINF, check=False)
        """Initial maximum moisture content in initial rooting depth zone"""
        if args.SMLIM is not None:
            self.parameterprovider.set_override("SMLIM", args.SMLIM, check=False)


        # WOFOST Parameters
        """Conversion factor for assimilates to leaves"""
        if args.CVL is not None:
            self.parameterprovider.set_override("CVL", args.CVL, check=False)
        """Conversion factor for assimilates to storage organs"""
        if args.CVO is not None:
            self.parameterprovider.set_override("CVO", args.CVO, check=False)
        """onversion factor for assimilates to roots"""  
        if args.CVR is not None:
            self.parameterprovider.set_override("CVR", args.CVR, check=False)
        """Conversion factor for assimilates to stems"""
        if args.CVS is not None:
            self.parameterprovider.set_override("CVS", args.CVS, check=False)

        # Assimilation Parameters
        """ Max leaf |CO2| assim. rate as a function of of DVS (kg/ha/hr)"""
        if args.AMAXTB is not None:
            self.parameterprovider.set_override("AMAXTB", args.AMAXTB, check=False)
        """ Light use effic. single leaf as a function of daily mean temperature |kg ha-1 hr-1 /(J m-2 s-1)|"""
        if args.EFFTB is not None:
            self.parameterprovider.set_override("EFFTB", args.EFFTB, check=False)
        """Extinction coefficient for diffuse visible as function of DVS"""
        if args.KDIFTB is not None:
            self.parameterprovider.set_override("KDIFTB", args.KDIFTB, check=False)
        """Reduction factor of AMAX as function of daily mean temperature"""
        if args.TMPFTB is not None:
            self.parameterprovider.set_override("TMPFTB", args.TMPFTB, check=False)
        """Reduction factor of AMAX as function of daily minimum temperature"""
        if args.TMNFTB is not None:
            self.parameterprovider.set_override("TMNFTB", args.TMNFTB, check=False)
        """Correction factor for AMAX given atmospheric CO2 concentration.""" 
        if args.CO2AMAXTB is not None:
            self.parameterprovider.set_override("CO2AMAXTB", args.CO2AMAXTB, check=False)
        """Correction factor for EFF given atmospheric CO2 concentration."""
        if args.CO2EFFTB is not None:
            self.parameterprovider.set_override("CO2EFFTB", args.CO2EFFTB, check=False)
        """Atmopheric CO2 concentration (ppm)"""
        if args.CO2 is not None:
            self.parameterprovider.set_override("CO2", args.CO2, check=False)

        # Evapotranspiration Parameters
        """Correction factor for potential transpiration rate"""
        if args.CFET is not None:
            self.parameterprovider.set_override("CFET", args.CFET, check=False)
        """Dependency number for crop sensitivity to soil moisture stress."""  
        if args.DEPNR is not None:
            self.parameterprovider.set_override("DEPNR", args.DEPNR, check=False)
        """Extinction coefficient for diffuse visible as function of DVS.""" 
        if args.KDIFTB is not None:
            self.parameterprovider.set_override("KDIFTB", args.KDIFTB, check=False)
        """Switch oxygen stress on (1) or off (0)"""
        if args.IOX is not None:
            self.parameterprovider.set_override("IOX", args.IOX, check=False)
        """Switch airducts on (1) or off (0) """ 
        if args.IAIRDU is not None:   
            self.parameterprovider.set_override("IAIRDU", args.IAIRDU, check=False)
        """Critical air content for root aeration"""  
        if args.CRAIRC is not None:
            self.parameterprovider.set_override("CRAIRC", args.CRAIRC, check=False)
        """Soil porosity"""
        if args.SM0 is not None:
            self.parameterprovider.set_override("SM0", args.SM0, check=False)
        """Volumetric soil moisture content at wilting point"""
        if args.SMW is not None:   
            self.parameterprovider.set_override("SMW", args.SMW, check=False)
        """Volumetric soil moisture content at field capacity"""  
        if args.SMFCF is not None:   
            self.parameterprovider.set_override("SMFCF", args.SMFCF, check=False)
        """Soil porosity"""    
        if args.SM0 is not None:
            self.parameterprovider.set_override("SM0", args.SM0, check=False)
        """Atmospheric CO2 concentration (ppm)"""  
        if args.CO2 is not None:
            self.parameterprovider.set_override("CO2", args.CO2, check=False)
        """Reduction factor for TRAMX as function of atmospheric CO2 concentration"""   
        if args.CO2TRATB is not None:   
            self.parameterprovider.set_override("CO2TRATB", args.CO2TRATB, check=False)
    
        # Leaf Dynamics Parameters
        """Maximum relative increase in LAI (ha / ha d)"""
        if args.RGRLAI is not None:
            self.parameterprovider.set_override("RGRLAI", args.RGRLAI, check=False)
        """Life span of leaves growing at 35 Celsius (days)""" 
        if args.SPAN is not None:         
            self.parameterprovider.set_override("SPAN", args.SPAN, check=False)
        """Lower threshold temp for ageing of leaves (C)""" 
        if args.TBASE is not None: 
            self.parameterprovider.set_override("TBASE", args.TBASE, check=False)
        """Max relative death rate of leaves due to water stress"""  
        if args.PERDL is not None:
            self.parameterprovider.set_override("PERDL", args.PERDL, check=False)
        """Initial total crop dry weight (kg/ha)"""
        if args.TDWI is not None:
            self.parameterprovider.set_override("TDWI", args.TDWI, check=False)
        """Extinction coefficient for diffuse visible light as function of DVS"""
        if args.KDIFTB is not None:
            self.parameterprovider.set_override("KDIFTB", args.KDIFTB, check=False)
        """Specific leaf area as a function of DVS (ha/kg)"""
        if args.SLATB is not None:
            self.parameterprovider.set_override("SLATB", args.SLATB, check=False)
        """Maximum relative death rate of leaves due to nutrient NPK stress"""
        if args.RDRNS is not None:  
            self.parameterprovider.set_override("RDRNS", args.RDRNS, check=False)
        """coefficient for the reduction due to nutrient NPK stress of the LAI increas
                (during juvenile phase)"""
        if args.NLAI is not None:
            self.parameterprovider.set_override("NLAI", args.NLAI, check=False)
        """Coefficient for the effect of nutrient NPK stress on SLA reduction""" 
        if args.NSLA is not None:
            self.parameterprovider.set_override("NSLA", args.NSLA, check=False)
        """Max. relative death rate of leaves due to nutrient NPK stress"""   
        if args.RDRN is not None:
            self.parameterprovider.set_override("RDRN", args.RDRN, check=False)
    
        # NPK Dynamics Parameters
        """Maximum N concentration in leaves as function of DVS (kg N / kg dry biomass)"""
        if args.NMAXLV_TB is not None:
            self.parameterprovider.set_override("NMAXLV_TB", args.NMAXLV_TB, check=False)
        """Maximum P concentration in leaves as function of DVS (kg P / kg dry biomass)"""
        if args.PMAXLV_TB is not None:
            self.parameterprovider.set_override("PMAXLV_TB", args.PMAXLV_TB, check=False) 
        """Maximum K concentration in leaves as function of DVS (kg K / kg dry biomass)"""
        if args.KMAXLV_TB is not None:
            self.parameterprovider.set_override("KMAXLV_TB", args.KMAXLV_TB, check=False)
        """Maximum N concentration in roots as fraction of maximum N concentration in leaves"""
        if args.NMAXRT_FR is not None:
            self.parameterprovider.set_override("NMAXRT_FR", args.NMAXRT_FR, check=False)
        """Maximum P concentration in roots as fraction of maximum P concentration in leaves"""
        if args.PMAXRT_FR is not None:
            self.parameterprovider.set_override("PMAXRT_FR", args.PMAXRT_FR, check=False)
        """Maximum K concentration in roots as fraction of maximum K concentration in leaves"""
        if args.KMAXRT_FR is not None:
            self.parameterprovider.set_override("KMAXRT_FR", args.KMAXRT_FR, check=False)
        """Maximum N concentration in stems as fraction of maximum N concentration in leaves"""
        if args.NMAXST_FR is not None:
            self.parameterprovider.set_override("NMAXST_FR", args.NMAXST_FR, check=False)
        """Maximum P concentration in stems as fraction of maximum P concentration in leaves"""
        if args.PMAXST_FR is not None:
            self.parameterprovider.set_override("PMAXST_FR", args.PMAXST_FR, check=False)
        """Maximum K concentration in stems as fraction of maximum K concentration in leaves"""
        if args.KMAXST_FR is not None:
            self.parameterprovider.set_override("KMAXST_FR", args.KMAXST_FR, check=False)   
        
        """Residual N fraction in leaves (kg N / kg dry biomass)"""
        if args.NRESIDLV is not None:
            self.parameterprovider.set_override("NRESIDLV", args.NRESIDLV, check=False) 
        """Residual P fraction in leaves (kg P / kg dry biomass)"""
        if args.PRESIDLV is not None:
            self.parameterprovider.set_override("PRESIDLV", args.PRESIDLV, check=False)
        """Residual K fraction in leaves (kg K / kg dry biomass)"""
        if args.KRESIDLV is not None:
            self.parameterprovider.set_override("KRESIDLV", args.KRESIDLV, check=False)

        """Residual N fraction in roots (kg N / kg dry biomass)"""
        if args.NRESIDRT is not None:
            self.parameterprovider.set_override("NRESIDRT", args.NRESIDRT, check=False)              
        """Residual P fraction in roots (kg P / kg dry biomass)"""
        if args.PRESIDRT is not None:
            self.parameterprovider.set_override("PRESIDRT", args.PRESIDRT, check=False)
        """Residual K fraction in roots (kg K / kg dry biomass)"""
        if args.KRESIDRT is not None:
            self.parameterprovider.set_override("KRESIDRT", args.KRESIDRT, check=False)
        """Residual N fraction in stems (kg N / kg dry biomass)"""
        if args.NRESIDST is not None:
            self.parameterprovider.set_override("NRESIDST", args.NRESIDST, check=False)
        """Residual P fraction in stems (kg P / kg dry biomass)"""  
        if args.PRESIDST is not None:                      
            self.parameterprovider.set_override("PRESIDST", args.PRESIDST, check=False)
        """Residual K fraction in stems (kg K / kg dry biomass)"""
        if args.KRESIDST is not None:
            self.parameterprovider.set_override("KRESIDST", args.KRESIDST, check=False)

        # Partioning Parameters
        """Partitioning to roots as a function of development stage"""
        if args.FRTB is not None:
            self.parameterprovider.set_override("FRTB", args.FRTB, check=False)
        """Partitioning to stems as a function of development stage"""
        if args.FSTB is not None:
            self.parameterprovider.set_override("FSTB", args.FSTB, check=False)
        """Partitioning to leaves as a function of development stage"""
        if args.FLTB is not None:
            self.parameterprovider.set_override("FLTB", args.FLTB, check=False)
        """Partitioning to starge organs as a function of development stage"""
        if args.FOTB is not None:
            self.parameterprovider.set_override("FOTB", args.FOTB, check=False)
        """Coefficient for the effect of N stress on leaf biomass allocation"""
        if args.NPART is not None:
            self.parameterprovider.set_override("NPART", args.NPART, check=False)
    
        # Vernalization Parameters
        """Saturated vernalisation requirements (days)"""
        if args.VERNSAT is not None:
            self.parameterprovider.set_override("VERNSAT", args.VERNSAT, check=False)
        """Base vernalisation requirements (days)"""
        if args.VERNBASE is not None:
            self.parameterprovider.set_override("VERNBASE", args.VERNBASE, check=False)
        """Rate of vernalisation as a function of daily mean temperature"""
        if args.VERNRTB is not None:
            self.parameterprovider.set_override("VERNRTB", args.VERNRTB, check=False)
        """Critical development stage after which the effect of vernalisation is halted"""
        if args.VERNDVS is not None:
            self.parameterprovider.set_override("VERNDVS", args.VERNDVS, check=False)

        # Phenology Parameters
        """Temperature sum from sowing to emergence (C day)"""
        if args.TSUMEM is not None:
            self.parameterprovider.set_override("TSUMEM", args.TSUMEM, check=False)
        """Base temperature for emergence (C)"""
        if args.TBASEM is not None:
            self.parameterprovider.set_override("TBASEM", args.TBASEM, check=False)
        """Maximum effective temperature for emergence (C day)"""
        if args.TEFFMX is not None:
            self.parameterprovider.set_override("TEFFMX", args.TEFFMX, check=False)
        """Temperature sum from emergence to anthesis (C day)"""
        if args.TSUM1 is not None:
            self.parameterprovider.set_override("TSUM1", args.TSUM1, check=False)
        """Temperature sum from anthesis to maturity (C day)"""
        if args.TSUM2 is not None:
            self.parameterprovider.set_override("TSUM2", args.TSUM2, check=False)
        """Switch for phenological development options temperature only (IDSL=0), 
        including daylength (IDSL=1) and including vernalization (IDSL>=2)"""
        if args.IDSL is not None:
            self.parameterprovider.set_override("IDSL", args.IDSL, check=False)
        """Optimal daylength for phenological development (hr)"""
        if args.DLO is not None:
            self.parameterprovider.set_override("DLO", args.DLO, check=False)
        """Critical daylength for phenological development (hr)"""
        if args.DLC is not None:
            self.parameterprovider.set_override("DLC", args.DLC, check=False)
        """Initial development stage at emergence. Usually this is zero, but it can 
        be higher or crops that are transplanted (e.g. paddy rice)"""
        if args.DVSI is not None:
            self.parameterprovider.set_override("DVSI", args.DVSI, check=False)
        """Final development stage"""
        if args.DVSEND is not None:
            self.parameterprovider.set_override("DVSEND", args.DVSEND, check=False)
        """Daily increase in temperature sum as a function of daily mean temperature (C)"""  
        if args.DTSMTB is not None:             
            self.parameterprovider.set_override("DTSMTB", args.DTSMTB, check=False)

        # Respiration Parameters
        """Relative increase in maintenance repiration rate with each 10 degrees increase in temperature"""
        if args.Q10 is not None:
            self.parameterprovider.set_override("Q10", args.Q10, check=False)
        """Relative maintenance respiration rate for roots |kg CH2O kg-1 d-1|"""
        if args.RMR is not None:
            self.parameterprovider.set_override("RMR", args.RMR, check=False)
        """ Relative maintenance respiration rate for stems |kg CH2O kg-1 d-1| """   
        if args.RMS is not None:
            self.parameterprovider.set_override("RMS", args.RMS, check=False)
        """Relative maintenance respiration rate for leaves |kg CH2O kg-1 d-1|""" 
        if args.RML is not None:
            self.parameterprovider.set_override("RML", args.RML, check=False)                              
        """Relative maintenance respiration rate for storage organs |kg CH2O kg-1 d-1|"""
        if args.RMO is not None:
            self.parameterprovider.set_override("RMO", args.RMO, check=False)

        # Root Dynamics Parameters
        """Initial rooting depth (cm)"""
        if args.RDI is not None:
            self.parameterprovider.set_override("RDI", args.RDI, check=False)
        """Daily increase in rooting depth  |cm day-1|"""
        if args.RRI is not None:
            self.parameterprovider.set_override("RRI", args.RRI, check=False)
        """Maximum rooting depth of the crop (cm)""" 
        if args.RDMCR is not None:
            self.parameterprovider.set_override("RDMCR", args.RDMCR, check=False)
        """Maximum rooting depth of the soil (cm)"""
        if args.RDMSOL is not None:
            self.parameterprovider.set_override("RDMSOL", args.RDMSOL, check=False)
        """Initial total crop dry weight |kg ha-1|"""
        if args.TDWI is not None:
            self.parameterprovider.set_override("TDWI", args.TDWI, check=False)
        """Presence of air ducts in the root (1) or not (0)""" 
        if args.IAIRDU is not None:
            self.parameterprovider.set_override("IAIRDU", args.IAIRDU, check=False)
        """Relative death rate of roots as a function of development stage"""
        if args.RDRRTB is not None:
            self.parameterprovider.set_override("RDRRTB", args.RDRRTB, check=False)

        # Stem Dynamics Parameters
        """Initial total crop dry weight (kg/ha)"""
        if args.TDWI is not None:
            self.parameterprovider.set_override("TDWI", args.TDWI, check=False)
        """Relative death rate of stems as a function of development stage"""
        if args.RDRSTB is not None:
            self.parameterprovider.set_override("RDRSTB", args.RDRSTB, check=False)
        """Specific Stem Area as a function of development stage (ha/kg)"""
        if args.SSATB is not None:
            self.parameterprovider.set_override("SSATB", args.SSATB, check=False)
    
        # Storage Organs Dynamics Parameters
        """Initial total crop dry weight (kg/ha)"""
        if args.TDWI is not None:
            self.parameterprovider.set_override("TDWI", args.TDWI, check=False) 
        """Specific Pod Area (ha / kg)""" 
        if args.SPA is not None:
            self.parameterprovider.set_override("SPA", args.SPA, check=False)
        
        # NPK Demand Uptake Parameters
        """Maximum N concentration in leaves as function of DVS (kg N / kg dry biomass)"""
        if args.NMAXLV_TB is not None:
            self.parameterprovider.set_override("NMAXLV_TB", args.NMAXLV_TB, check=False)
        """Maximum P concentration in leaves as function of DVS (kg P / kg dry biomass)"""
        if args.PMAXLV_TB is not None:
            self.parameterprovider.set_override("PMAXLV_TB", args.PMAXLV_TB, check=False)
        """Maximum K concentration in leaves as function of DVS (kg K / kg dry biomass)"""
        if args.KMAXLV_TB is not None:
            self.parameterprovider.set_override("KMAXLV_TB", args.KMAXLV_TB, check=False)
        """ Maximum N concentration in roots as fraction of maximum N concentration in leaves"""
        if args.NMAXRT_FR is not None:
            self.parameterprovider.set_override("NMAXRT_FR", args.NMAXRT_FR, check=False)
        """Maximum P concentration in roots as fraction of maximum P concentration in leaves"""
        if args.PMAXRT_FR is not None:
            self.parameterprovider.set_override("PMAXRT_FR", args.PMAXRT_FR, check=False)   
        """Maximum K concentration in roots as fraction  of maximum K concentration in leaves"""
        if args.KMAXRT_FR is not None:
            self.parameterprovider.set_override("KMAXRT_FR", args.KMAXRT_FR, check=False)  
        """Maximum N concentration in stems as fraction of maximum N concentration in leaves"""
        if args.NMAXST_FR is not None:
            self.parameterprovider.set_override("NMAXST_FR", args.NMAXST_FR, check=False)
        """Maximum P concentration in stems as fraction of maximum P concentration in leaves"""
        if args.PMAXST_FR is not None:
            self.parameterprovider.set_override("PMAXST_FR", args.PMAXST_FR, check=False)
        """Maximum K concentration in stems as fraction of maximum K concentration in leaves"""
        if args.KMAXST_FR is not None:
            self.parameterprovider.set_override("KMAXST_FR", args.KMAXST_FR, check=False)
        """ Maximum N concentration in storage organs (kg N / kg dry biomass)"""
        if args.NMAXSO is not None:
            self.parameterprovider.set_override("NMAXSO", args.NMAXSO, check=False)
        """Maximum P concentration in storage organs (kg P / kg dry biomass)"""
        if args.PMAXSO is not None:  
            self.parameterprovider.set_override("PMAXSO", args.PMAXSO, check=False)
        """Maximum K concentration in storage organs (kg K / kg dry biomass)""" 
        if args.KMAXSO is not None:         
            self.parameterprovider.set_override("KMAXSO", args.KMAXSO, check=False)
        """Critical N concentration as fraction of maximum N concentration for vegetative
                        plant organs as a whole (leaves + stems)"""
        if args.NCRIT_FR is not None:
            self.parameterprovider.set_override("NCRIT_FR", args.NCRIT_FR, check=False)
        """Critical P concentration as fraction of maximum P concentration for vegetative
                        plant organs as a whole (leaves + stems)"""
        if args.PCRIT_FR is not None:
            self.parameterprovider.set_override("PCRIT_FR", args.PCRIT_FR, check=False)
        """Critical K concentration as fraction of maximum K concentration for vegetative
                        plant organs as a whole (leaves + stems)"""
        if args.KCRIT_FR is not None:
            self.parameterprovider.set_override("KCRIT_FR", args.KCRIT_FR, check=False)
        
        """Time coefficient for N translation to storage organs (days)"""
        if args.TCNT is not None:
            self.parameterprovider.set_override("TCNT", args.TCNT, check=False)
        """Time coefficient for P translation to storage organs (days)"""
        if args.TCPT is not None:
            self.parameterprovider.set_override("TCPT", args.TCPT, check=False)    
        """Time coefficient for K translation to storage organs (days)"""
        if args.TCKT is not None:
            self.parameterprovider.set_override("TCKT", args.TCKT, check=False)
        """fraction of crop nitrogen uptake by biological fixation (kg N / kg dry biomass)"""
        if args.NFIX_FR is not None:
            self.parameterprovider.set_override("NFIX_FR", args.NFIX_FR, check=False)
        """Maximum rate of N uptake (kg N / ha day)"""
        if args.RNUPTAKEMAX is not None:
            self.parameterprovider.set_override("RNUPTAKEMAX", args.RNUPTAKEMAX, check=False)
        """Maximum rate of P uptake (kg P / ha day)"""
        if args.RPUPTAKEMAX is not None:
            self.parameterprovider.set_override("RPUPTAKEMAX", args.RPUPTAKEMAX, check=False)
        """Maximum rate of K uptake (kg K / ha day)"""
        if args.RKUPTAKEMAX is not None:
            self.parameterprovider.set_override("RKUPTAKEMAX", args.RKUPTAKEMAX, check=False)     

        # NPK Stress Parameters
        """Maximum N concentration in leaves as function of DVS (kg N kg-1 dry biomass)"""
        if args.NMAXLV_TB is not None:
            self.parameterprovider.set_override("NMAXLV_TB", args.NMAXLV_TB, check=False)   
        """Maximum P concentration in leaves as function of DVS (kg N / kg dry biomass)"""
        if args.PMAXLV_TB is not None:
            self.parameterprovider.set_override("PMAXLV_TB", args.PMAXLV_TB, check=False)
        """Maximum K concentration in leaves as function of DVS (kg N / kg dry biomass)"""
        if args.KMAXLV_TB is not None:
            self.parameterprovider.set_override("KMAXLV_TB", args.KMAXLV_TB, check=False)
        """Maximum N concentration in roots as fraction of maximum N concentration in leaves"""
        if args.NMAXRT_FR is not None:
            self.parameterprovider.set_override("NMAXRT_FR", args.NMAXRT_FR, check=False)
        """Maximum P concentration in roots as fraction of maximum P concentration in leaves"""
        if args.PMAXRT_FR is not None:
            self.parameterprovider.set_override("PMAXRT_FR", args.PMAXRT_FR, check=False)
        """Maximum K concentration in roots as fraction of maximum K concentration in leaves"""
        if args.KMAXRT_FR is not None:
            self.parameterprovider.set_override("KMAXRT_FR", args.KMAXRT_FR, check=False)
        """Maximum N concentration in stems as fraction of maximum N concentration in leaves"""
        if args.NMAXST_FR is not None:
            self.parameterprovider.set_override("NMAXST_FR", args.NMAXST_FR, check=False)
        """Maximum P concentration in stems as fraction of maximum P concentration in leaves"""
        if args.PMAXST_FR is not None:
            self.parameterprovider.set_override("PMAXST_FR", args.PMAXST_FR, check=False)  
        """Maximum K concentration in stems as fraction of maximum K concentration in leaves"""
        if args.KMAXST_FR is not None:
            self.parameterprovider.set_override("KMAXST_FR", args.KMAXST_FR, check=False)
        """Critical N concentration as fraction of maximum N concentration for vegetative
                        plant organs as a whole (leaves + stems)"""
        if args.NCRIT_FR is not None:
            self.parameterprovider.set_override("NCRIT_FR", args.NCRIT_FR, check=False)  
        """Critical P concentration as fraction of maximum P concentration for vegetative
                        plant organs as a whole (leaves + stems)"""
        if args.PCRIT_FR is not None:
            self.parameterprovider.set_override("PCRIT_FR", args.PCRIT_FR, check=False)    
        """Critical K concentration as fraction of maximum L concentration for 
        vegetative plant organs as a whole (leaves + stems)"""
        if args.KCRIT_FR is not None:
            self.parameterprovider.set_override("KCRIT_FR", args.KCRIT_FR, check=False)
        """Residual N fraction in leaves (kg N / kg dry biomass)"""
        if args.NRESIDLV is not None:
            self.parameterprovider.set_override("NRESIDLV", args.NRESIDLV, check=False)
        """Residual P fraction in leaves (kg P / kg dry biomass)"""
        if args.PRESIDLV is not None:
            self.parameterprovider.set_override("PRESIDLV", args.PRESIDLV, check=False)
        """Residual K fraction in leaves (kg K / kg dry biomass)"""
        if args.KRESIDLV is not None:
            self.parameterprovider.set_override("KRESIDLV", args.KRESIDLV, check=False)               
        """Residual N fraction in stems (kg N / kg dry biomass)"""
        if args.NRESIDST is not None:
            self.parameterprovider.set_override("NRESIDST", args.NRESIDST, check=False)
        """Residual P fraction in stems (kg P/ kg dry biomass)"""
        if args.PRESIDST is not None:
            self.parameterprovider.set_override("PRESIDST", args.PRESIDST, check=False)
        """Residual K fraction in stems (kg K/ kg dry biomass)"""
        if args.KRESIDST is not None:
            self.parameterprovider.set_override("KRESIDST", args.KRESIDST, check=False)   
        """Coefficient for the reduction of RUE due to nutrient (N-P-K) stress"""
        if args.NLUE_NPK is not None:
            self.parameterprovider.set_override("NLUE_NPK", args.NLUE_NPK, check=False)
    
        # NPK Translocation Parameters
        """Residual N fraction in leaves (kg N / kg dry biomass)""" 
        if args.NRESIDLV is not None:
            self.parameterprovider.set_override("NRESIDLV", args.NRESIDLV, check=False)
        """Residual P fraction in leaves (kg P / kg dry biomass)""" 
        if args.PRESIDLV is not None:
            self.parameterprovider.set_override("PRESIDLV", args.PRESIDLV, check=False)
        """Residual K fraction in leaves (kg K / kg dry biomass)"""
        if args.KRESIDLV is not None: 
            self.parameterprovider.set_override("KRESIDLV", args.KRESIDLV, check=False)  
        """Residual N fraction in stems (kg N / kg dry biomass)""" 
        if args.NRESIDST is not None:
            self.parameterprovider.set_override("NRESIDST", args.NRESIDST, check=False)
        """Residual K fraction in stems (kg P / kg dry biomass)"""
        if args.PRESIDST is not None: 
            self.parameterprovider.set_override("PRESIDST", args.PRESIDST, check=False)
        """Residual P fraction in stems (kg K / kg dry biomass)"""
        if args.KRESIDST is not None: 
            self.parameterprovider.set_override("KRESIDST", args.KRESIDST, check=False)      
        """NPK translocation from roots as a fraction of resp. total NPK amounts translocated
                            from leaves and stems"""
        if args.NPK_TRANSLRT_FR is not None:
            self.parameterprovider.set_override("NPK_TRANSLRT_FR", args.NPK_TRANSLRT_FR, check=False)

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
        location = self.location
        if self.location is None:
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

        if 'year' in kwargs:
            self.year = kwargs['year']
        if 'location' in kwargs:
            self.location = kwargs['location']

        # Reset to random year if flag
        if self.random_reset:
            self.crop_start_date, self.crop_end_date = self._random_year()
        else:
            self.crop_start_date = \
                list(self.agromanagement[0].values())[0]['CropCalendar']['crop_start_date']
            self.crop_end_date = \
                list(self.agromanagement[0].values())[0]['CropCalendar']['crop_end_date']
            self.crop_start_date = self.crop_start_date.replace(year=self.year)
            self.crop_end_date = self.crop_end_date.replace(year=self.year)
        
        # Change to the new year specified by self.year
        self.date = self.crop_start_date
        old_campaign_start = self.campaign_start
        self.campaign_start = self.campaign_start.replace(year=self.year)
        self.agromanagement[0][self.campaign_start] = self.agromanagement[0].pop(old_campaign_start)

        self.agromanagement[0][self.campaign_start]['CropCalendar']['crop_start_date'] = \
            self.agromanagement[0][self.campaign_start]['CropCalendar']['crop_start_date'].replace(year=self.year)
        self.agromanagement[0][self.campaign_start]['CropCalendar']['crop_end_date'] = \
            self.agromanagement[0][self.campaign_start]['CropCalendar']['crop_end_date'].replace(year=self.year)
    
        # Reset weather 
        self.weatherdataprovider = self._get_weatherdataprovider()

        # Override parameters
        self._set_params(self.wofost_params)

        # Reset model
        self.model = pcse.models.Wofost80(self.parameterprovider, self.weatherdataprovider,
                                         self.agromanagement, config=self.config)
        
        # Generate first part of output 
        output = self._run_simulation()
        observation = self._process_output(output)

        return observation, self.log

    # Step through the environment
    def step(self, action):
        npk, irrigation = self._take_action(action)
        output = self._run_simulation()

        observation = self._process_output(output)
        
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
        self.date = output.index[-1]

        # Observed weather until next intervention time
        weather_observation = self._get_weather(self.weatherdataprovider, self.date,
                                             self.intervention_interval)

        # Count the number of days elapsed - useful to have in observation space
        # for time based policies
        days_elapsed = self.date - self.crop_start_date

        observation = np.concatenate([crop_observation, weather_observation.flatten(), [days_elapsed.days]])
        observation = np.nan_to_num(observation)

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
        '''reward = output.iloc[-1]['WSO'] - \
                        (np.sum(self.beta * np.array([n_amount, p_amount, k_amount])) \
                        - .25 * self.beta * irrig_amount)'''
        reward = output.iloc[-1]['WSO']
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
        self.config="Wofost80_PP.conf"
        super().__init__(args)

# Simulating production under abundant water but limited NPK dynamics
class Limited_NPK_Env(NPK_Env):

    def __init__(self, args):
        self.config = "Wofost80_LNPK.conf"
        super().__init__(args)

# Simulating production under limited Nitrogen but abundant water and P/K
class Limited_N_Env(NPK_Env):

    def __init__(self, args):
        self.config = "Wofost80_LN.conf"
        super().__init__(args)

# Simulating production under limited water and Nitrogen
class Limited_NW_Env(NPK_Env):

    def __init__(self, args):
        self.config = "Wofost80_LNW.conf"
        super().__init__(args)

# Simulating production under limited water 
class Limited_W_Env(NPK_Env):
    def __init__(self, args):
        self.config = "Wofost80_LW.conf"
        super().__init__(args)
