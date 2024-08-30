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
        self.model = pcse.models.Wofost80(self.parameterprovider, self.weatherdataprovider,
                                         self.agromanagement, config=self.config)
        self.date = self.crop_start_date

        self._set_params(args)

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

    def _set_params(self, args):
            # All editable parameters for the WOFOST crop and soil. If left to default
        # of None, values will be drawn from the .yaml files in /env_config/
        # NPK Soil dynamics params
        """Base soil supply of N available through mineralization kg/ha"""
        if args.NSOILBASE is not None:
            self.model.soil.NPK_Soil_Dynamics.params.NSOILBASE = args.NSOILBASE   
        """Fraction of base soil N that comes available every day"""    
        if args.NSOILBASE_FR is not None:     
            self.model.soil.NPK_Soil_Dynamics.params.NSOILBASE_FR
        """Base soil supply of P available through mineralization kg/ha"""
        if args.PSOILBASE is not None:
            self.model.soil.NPK_Soil_Dynamics.params.PSOILBASE 
        """Fraction of base soil P that comes available every day"""         
        if args.PSOILBASE_FR is not None:
            self.model.soil.NPK_Soil_Dynamics.params.PSOILBASE_FR
        """Base soil supply of K available through mineralization kg/ha"""
        if args.KSOILBASE is not None:
            self.model.soil.NPK_Soil_Dynamics.params.KSOILBASE 
        """Fraction of base soil K that comes available every day""" 
        if args.KSOILBASE_FR is not None:        
            self.model.soil.NPK_Soil_Dynamics.params.KSOILBASE_FR
        """Initial N available in the N pool (kg/ha)"""
        if args.NAVAILI is not None:
            self.model.soil.NPK_Soil_Dynamics.params.NAVAILI
        """Initial P available in the P pool (kg/ha)"""
        if args.PAVAILI is not None:
            self.model.soil.NPK_Soil_Dynamics.params.PAVAILI
        """Initial K available in the K pool (kg/ha)"""
        if args.KAVAILI is not None:
            self.model.soil.NPK_Soil_Dynamics.params.KAVAILI
        """Background supply of N through atmospheric deposition (kg/ha/day)"""
        if args.BG_N_SUPPLY is not None:
            self.model.soil.NPK_Soil_Dynamics.params.BG_N_SUPPLY
        """Background supply of P through atmospheric deposition (kg/ha/day)"""
        if args.BG_P_SUPPLY is not None:
            self.model.soil.NPK_Soil_Dynamics.params.BG_P_SUPPLY
        """Background supply of K through atmospheric deposition (kg/ha/day)"""
        if args.BG_K_SUPPLY is not None:
            self.model.soil.NPK_Soil_Dynamics.params.BG_K_SUPPLY

        # Waterbalance soil dynamics params
        """Field capacity of the soil"""
        if args.SMFCF is not None:
            self.model.soil.WaterbalanceFD.params.SMFCF = args.SMFCF             
        """Porosity of the soil"""
        if args.SM0 is not None:
            self.model.soil.WaterbalanceFD.params.SM0 = args.SM0                            
        """Wilting point of the soil"""
        if args.SMW is not None:    
            self.model.soil.WaterbalanceFD.params.SMW = args.SMW                    
        """Soil critical air content (waterlogging)"""
        if args.CRAIRC is not None:
            self.model.soil.WaterbalanceFD.params.CRAIRC = args.CRAIRC    
        """maximum percolation rate root zone (cm/day)"""
        if args.SOPE is not None:
            self.model.soil.WaterbalanceFD.params.SOPE = args.SOPE
        """maximum percolation rate subsoil (cm/day)"""
        if args.KSUB is not None:
            self.model.soil.WaterbalanceFD.params.KSUB = args.KSUB           
        """Soil rootable depth (cm)"""
        if args.RDMSOL is not None:
            self.model.soil.WaterbalanceFD.params.RDMSOL = args.RDMSOL                         
        """Indicates whether non-infiltrating fraction of rain is a function of storm size (1) or not (0)"""
        if args.IFUNRN is not None:
            self.model.soil.WaterbalanceFD.params.IFUNRN = args.IFUNRN
        """Maximum surface storage (cm)"""                               
        if args.SSMAX is not None:
            self.model.soil.WaterbalanceFD.params.SSMAX = args.SSMAX                   
        """Initial surface storage (cm)"""
        if args.SSI is not None:
            self.model.soil.WaterbalanceFD.params.SSI = args.SSI            
        """Initial amount of water in total soil profile (cm)"""
        if args.WAV is not None:
            self.model.soil.WaterbalanceFD.params.WAV = args.WAV
        """Maximum fraction of rain not-infiltrating into the soil"""
        if args.NOTINF is not None:   
            self.model.soil.WaterbalanceFD.params.NOTINF = args.NOTINF
        """Initial maximum moisture content in initial rooting depth zone"""
        if args.SMLIM is not None:
            self.model.soil.WaterbalanceFD.params.SMLIM = args.SMLIM


        # WOFOST Parameters
        """Conversion factor for assimilates to leaves"""
        if args.CVL is not None:
            self.model.crop.params.CVL = args.CVL
        """Conversion factor for assimilates to storage organs"""
        if args.CVO is not None:
            self.model.crop.params.CVO = args.CVO
        """onversion factor for assimilates to roots"""  
        if args.CVR is not None:
            self.model.crop.params.CVR = args.CVR
        """Conversion factor for assimilates to stems"""
        if args.CVS is not None:
            self.model.crop.params.CVS = args.CVS

        # Assimilation Parameters
        """ Max leaf |CO2| assim. rate as a function of of DVS (kg/ha/hr)"""
        if args.AMAXTB is not None:
            self.model.crop.assim.params.AMAXTB = args.AMAXTB
        """ Light use effic. single leaf as a function of daily mean temperature |kg ha-1 hr-1 /(J m-2 s-1)|"""
        if args.EFFTB is not None:
            self.model.crop.assim.params.EFFTB = args.EFFTB
        """Extinction coefficient for diffuse visible as function of DVS"""
        if args.KDIFTB is not None:
            self.model.crop.assim.params.KDIFTB = args.KDIFTB
        """Reduction factor of AMAX as function of daily mean temperature"""
        if args.TMPFTB is not None:
            self.model.crop.assim.params.TMPFTB = args.TMPFTB
        """Reduction factor of AMAX as function of daily minimum temperature"""
        if args.TMNFTB is not None:
            self.model.crop.assim.params.TMNFTB = args.TMNFTB
        """Correction factor for AMAX given atmospheric CO2 concentration.""" 
        if args.CO2AMAXTB is not None:
            self.model.crop.assim.params.CO2AMAXTB = args.CO2AMAXTB
        """Correction factor for EFF given atmospheric CO2 concentration."""
        if args.CO2EFFTB is not None:
            self.model.crop.assim.params.CO2EFFTB = args.CO2EFFTB
        """Atmopheric CO2 concentration (ppm)"""
        if args.CO2 is not None:
            self.model.crop.assim.params.CO2 = args.CO2

        # Evapotranspiration Parameters
        """Correction factor for potential transpiration rate"""
        if args.CFET is not None:
            self.model.crop.evtra.params.CFET = args.CFET
        """Dependency number for crop sensitivity to soil moisture stress."""  
        if args.DEPNR is not None:
            self.model.crop.evtra.params.DEPNR = args.DEPNR
        """Extinction coefficient for diffuse visible as function of DVS.""" 
        if args.KDIFTB is not None:
            self.model.crop.evtra.params.KDIFTB = args.KDIFTB
        """Switch oxygen stress on (1) or off (0)"""
        if args.IOX is not None:
            self.model.crop.evtra.params.IOX = args.IOX
        """Switch airducts on (1) or off (0) """ 
        if args.IAIRDU is not None:   
            self.model.crop.evtra.params.IAIRDU = args.IAIRDU
        """Critical air content for root aeration"""  
        if args.CRAIRC is not None:
            self.model.crop.evtra.params.CRAIRC = args.CRAIRC
        """Soil porosity"""
        if args.SM0 is not None:
            self.model.crop.evtra.params.SM0 = args.SM0
        """Volumetric soil moisture content at wilting point"""
        if args.SMW is not None:   
            self.model.crop.evtra.params.SMW = args.SMW
        """Volumetric soil moisture content at field capacity"""  
        if args.SMFCF is not None:   
            self.model.crop.evtra.params.SMCFC = args.SMFCF
        """Soil porosity"""    
        if args.SM0 is not None:
            self.model.crop.evtra.params.SM0 = args.SM0
        """Atmospheric CO2 concentration (ppm)"""  
        if args.CO2 is not None:
            self.model.crop.evtra.params.CO2 = args.CO2
        """Reduction factor for TRAMX as function of atmospheric CO2 concentration"""   
        if args.CO2TRATB is not None:   
            self.model.crop.evtra.params.CO2TRATB = args.CO2TRATB
    
        # Leaf Dynamics Parameters
        """Maximum relative increase in LAI (ha / ha d)"""
        if args.RGRLAI is not None:
            self.model.crop.lv_dynamics.params.RGRLAI = args.RGRLAI    
        """Life span of leaves growing at 35 Celsius (days)""" 
        if args.SPAN is not None:         
            self.model.crop.lv_dynamics.params.SPAN = args.SPAN
        """Lower threshold temp for ageing of leaves (C)""" 
        if args.TBASE is not None: 
            self.model.crop.lv_dynamics.params.TBASE = args.TBASE
        """Max relative death rate of leaves due to water stress"""  
        if args.PERDL is not None:
            self.model.crop.lv_dynamics.params.PERDL = args.PERDL  
        """Initial total crop dry weight (kg/ha)"""
        if args.TDWI is not None:
            self.model.crop.lv_dynamics.params.TDWI = args.TDWI
        """Extinction coefficient for diffuse visible light as function of DVS"""
        if args.KDIFTB is not None:
            self.model.crop.lv_dynamics.params.KDIFTB = args.KDIFTB 
        """Specific leaf area as a function of DVS (ha/kg)"""
        if args.SLATB is not None:
            self.model.crop.lv_dynamics.params.SLATB = args.SLATB
        """Maximum relative death rate of leaves due to nutrient NPK stress"""
        if args.RDRNS is not None:  
            self.model.crop.lv_dynamics.params.RDRNS = args.RDRNS  
        """coefficient for the reduction due to nutrient NPK stress of the LAI increas
                (during juvenile phase)"""
        if args.NLAI is not None:
            self.model.crop.lv_dynamics.params.NLAI = args.NLAI  
        """Coefficient for the effect of nutrient NPK stress on SLA reduction""" 
        if args.NSLA is not None:
            self.model.crop.lv_dynamics.params.NSLA = args.NSLA
        """Max. relative death rate of leaves due to nutrient NPK stress"""   
        if args.RDRN is not None:
            self.model.crop.lv_dynamics.params.RDRN = args.RDRN
    
        # NPK Dynamics Parameters
        """Maximum N concentration in leaves as function of DVS (kg N / kg dry biomass)"""
        if args.NMAXLV_TB is not None:
            self.model.crop.npk_crop_dynamics.params.NMAXLV_TB = args.NMAXLV_TB 
        """Maximum P concentration in leaves as function of DVS (kg P / kg dry biomass)"""
        if args.PMAXLV_TB is not None:
            self.model.crop.npk_crop_dynamics.params.PMAXLV_TB = args.PMAXLV_TB    
        """Maximum K concentration in leaves as function of DVS (kg K / kg dry biomass)"""
        if args.KMAXLV_TB is not None:
            self.model.crop.npk_crop_dynamics.params.KMAXLV_TB = args.KMAXLV_TB    
        """Maximum N concentration in roots as fraction of maximum N concentration in leaves"""
        if args.NMAXRT_FR is not None:
            self.model.crop.npk_crop_dynamics.params.NMAXRT_FR = args.NMAXRT_FR   
        """Maximum P concentration in roots as fraction of maximum P concentration in leaves"""
        if args.PMAXRT_FR is not None:
            self.model.crop.npk_crop_dynamics.params.PMAXRT_FR = args.PMAXRT_FR
        """Maximum K concentration in roots as fraction of maximum K concentration in leaves"""
        if args.KMAXRT_FR is not None:
            self.model.crop.npk_crop_dynamics.params.KMAXRT_FR = args.KMAXRT_FR 
        """Maximum N concentration in stems as fraction of maximum N concentration in leaves"""
        if args.NMAXST_FR is not None:
            self.model.crop.npk_crop_dynamics.params.NMAXST_FR = args.NMAXST_FR    
        """Maximum P concentration in stems as fraction of maximum P concentration in leaves"""
        if args.PMAXST_FR is not None:
            self.model.crop.npk_crop_dynamics.params.PMAXST_FR = args.PMAXST_FR
        """Maximum K concentration in stems as fraction of maximum K concentration in leaves"""
        if args.KMAXST_FR is not None:
            self.model.crop.npk_crop_dynamics.params.KMAXST_FR = args.KMAXST_FR    
        
        """Residual N fraction in leaves (kg N / kg dry biomass)"""
        if args.NRESIDLV is not None:
            self.model.crop.npk_crop_dynamics.params.NRESIDLV = args.NRESIDLV     
        """Residual P fraction in leaves (kg P / kg dry biomass)"""
        if args.PRESIDLV is not None:
            self.model.crop.npk_crop_dynamics.params.PRESIDLV = args.PRESIDLV  
        """Residual K fraction in leaves (kg K / kg dry biomass)"""
        if args.KRESIDLV is not None:
            self.model.crop.npk_crop_dynamics.params.KRESIDLV = args.KRESIDLV     

        """Residual N fraction in roots (kg N / kg dry biomass)"""
        if args.NRESIDRT is not None:
            self.model.crop.npk_crop_dynamics.params.NRESIDRT = args.NRESIDRT                            
        """Residual P fraction in roots (kg P / kg dry biomass)"""
        if args.PRESIDRT is not None:
            self.model.crop.npk_crop_dynamics.params.PRESIDRT = args.PRESIDRT     
        """Residual K fraction in roots (kg K / kg dry biomass)"""
        if args.KRESIDRT is not None:
            self.model.crop.npk_crop_dynamics.params.KRESIDRT = args.KRESIDRT     
        """Residual N fraction in stems (kg N / kg dry biomass)"""
        if args.NRESIDST is not None:
            self.model.crop.npk_crop_dynamics.params.NRESIDST = args.NRESIDST  
        """Residual P fraction in stems (kg P / kg dry biomass)"""  
        if args.PRESIDST is not None:                      
            self.model.crop.npk_crop_dynamics.params.PRESIDST = args.PRESIDST    
        """Residual K fraction in stems (kg K / kg dry biomass)"""
        if args.KRESIDST is not None:
            self.model.crop.npk_crop_dynamics.params.KRESIDST = args.KRESIDST     

        # Partioning Parameters
        """Partitioning to roots as a function of development stage"""
        if args.FRTB is not None:
            self.model.crop.part.params.FRTB = args.FRTB   
        """Partitioning to stems as a function of development stage"""
        if args.FSTB is not None:
            self.model.crop.part.params.FSTB = args.FSTB   
        """Partitioning to leaves as a function of development stage"""
        if args.FLTB is not None:
            self.model.crop.part.params.FLTB = args.FLTB   
        """Partitioning to starge organs as a function of development stage"""
        if args.FOTB is not None:
            self.model.crop.part.params.FOTB = args.FOTB   
        """Coefficient for the effect of N stress on leaf biomass allocation"""
        if args.NPART is not None:
            self.model.crop.part.params.NPART = args.NPART  
    
        # Vernalization Parameters
        """Saturated vernalisation requirements (days)"""
        if args.VERNSAT is not None:
            self.model.crop.pheno.vernalisation.params.VERNSAT = args.VERNSAT
        """Base vernalisation requirements (days)"""
        if args.VERNBASE is not None:
            self.model.crop.pheno.vernalisation.params.VERNBASE = args.VERNBASE
        """Rate of vernalisation as a function of daily mean temperature"""
        if args.VERNRTB is not None:
            self.model.crop.pheno.vernalisation.params.VERNRTB = args.VERNRTB
        """Critical development stage after which the effect of vernalisation is halted"""
        if args.VERNDVS is not None:
            self.model.crop.pheno.vernalisation.params.VERNDVS = args.VERNDVS

        # Phenology Parameters
        """Temperature sum from sowing to emergence (C day)"""
        if args.TSUMEM is not None:
            self.model.crop.pheno.params.TSUMEM = args.TSUMEM
        """Base temperature for emergence (C)"""
        if args.TBASEM is not None:
            self.model.crop.pheno.params.TBASEM = args.TBASEM
        """Maximum effective temperature for emergence (C day)"""
        if args.TEFFMX is not None:
            self.model.crop.pheno.params.TEFFMX = args.TEFFMX
        """Temperature sum from emergence to anthesis (C day)"""
        if args.TSUM1 is not None:
            self.model.crop.pheno.params.TSUM1 = args.TSUM1
        """Temperature sum from anthesis to maturity (C day)"""
        if args.TSUM2 is not None:
            self.model.crop.pheno.params.TSUM2 = args.TSUM2
        """Switch for phenological development options temperature only (IDSL=0), 
        including daylength (IDSL=1) and including vernalization (IDSL>=2)"""
        if args.IDSL is not None:
            self.model.crop.pheno.params.IDSL = args.IDSL
        """Optimal daylength for phenological development (hr)"""
        if args.DLO is not None:
            self.model.crop.pheno.params.DLO = args.DLO
        """Critical daylength for phenological development (hr)"""
        if args.DLC is not None:
            self.model.crop.pheno.params.DLC = args.DLC
        """Initial development stage at emergence. Usually this is zero, but it can 
        be higher or crops that are transplanted (e.g. paddy rice)"""
        if args.DVSI is not None:
            self.model.crop.pheno.params.DVSI = args.DVSI
        """Final development stage"""
        if args.DVSEND is not None:
            self.model.crop.pheno.params.DVSEND = args.DVSEND    
        """Daily increase in temperature sum as a function of daily mean temperature (C)"""  
        if args.DTSMTB is not None:             
            self.model.crop.pheno.params.DTSMTB = args.DTSMTB

        # Respiration Parameters
        """Relative increase in maintenance repiration rate with each 10 degrees increase in temperature"""
        if args.Q10 is not None:
            self.model.crop.mres.params.Q10 = args.Q10
        """Relative maintenance respiration rate for roots |kg CH2O kg-1 d-1|"""
        if args.RMR is not None:
            self.model.crop.mres.params.RMR = args.RMR
        """ Relative maintenance respiration rate for stems |kg CH2O kg-1 d-1| """   
        if args.RMS is not None:
            self.model.crop.mres.params.RMS = args.RMS
        """Relative maintenance respiration rate for leaves |kg CH2O kg-1 d-1|""" 
        if args.RML is not None:
            self.model.crop.mres.params.RML = args.RML                                      
        """Relative maintenance respiration rate for storage organs |kg CH2O kg-1 d-1|"""
        if args.RMO is not None:
            self.model.crop.mres.params.RMO = args.RMO  

        # Root Dynamics Parameters
        """Initial rooting depth (cm)"""
        if args.RDI is not None:
            self.model.crop.ro_dynamics.params.RDI = args.RDI
        """Daily increase in rooting depth  |cm day-1|"""
        if args.RRI is not None:
            self.model.crop.ro_dynamics.params.RRI = args.RRI 
        """Maximum rooting depth of the crop (cm)""" 
        if args.RDMCR is not None:
            self.model.crop.ro_dynamics.params.RDMCR = args.RDMCR
        """Maximum rooting depth of the soil (cm)"""
        if args.RDMSOL is not None:
            self.model.crop.ro_dynamics.params.RDMSOL = args.RDMSOL
        """Initial total crop dry weight |kg ha-1|"""
        if args.TDWI is not None:
            self.model.crop.ro_dynamics.params.TDWI = args.TDWI
        """Presence of air ducts in the root (1) or not (0)""" 
        if args.IAIRDU is not None:
            self.model.crop.ro_dynamics.params.IAIRDU = args.IAIRDU
        """Relative death rate of roots as a function of development stage"""
        if args.RDRRTB is not None:
            self.model.crop.ro_dynamics.params.RDRRTB = args.RDRRTB

        # Stem Dynamics Parameters
        """Initial total crop dry weight (kg/ha)"""
        if args.TDWI is not None:
            self.model.crop.st_dynamics.params.TDWI = args.TDWI   
        """Relative death rate of stems as a function of development stage"""
        if args.RDRSTB is not None:
            self.model.crop.st_dynamics.params.RDRSTB = args.RDRSTB 
        """Specific Stem Area as a function of development stage (ha/kg)"""
        if args.SSATB is not None:
            self.model.crop.st_dynamics.params.SSATB = args.SSATB
    
        # Storage Organs Dynamics Parameters
        """Initial total crop dry weight (kg/ha)"""
        if args.TDWI is not None:
            self.model.crop.so_dynamics.params.TDWI = args.TDWI  
        """Specific Pod Area (ha / kg)""" 
        if args.SPA is not None:
            self.model.crop.so_dynamics.params.SPA = args.SPA  
        
        # NPK Demand Uptake Parameters
        """Maximum N concentration in leaves as function of DVS (kg N / kg dry biomass)"""
        if args.NMAXLV_TB is not None:
            self.model.crop.npk_crop.demand_uptake.NMAXLV_TB = args.NMAXLV_TB    
        """Maximum P concentration in leaves as function of DVS (kg P / kg dry biomass)"""
        if args.NMAXLV_TB is not None:
            self.model.crop.npk_crop.demand_uptake.NMAXLV_TB  = args.NMAXLV_TB  
        """Maximum K concentration in leaves as function of DVS (kg K / kg dry biomass)"""
        if args.KMAXLV_TB is not None:
            self.model.crop.npk_crop.demand_uptake.KMAXLV_TB = args.KMAXLV_TB    
        """ Maximum N concentration in roots as fraction of maximum N concentration in leaves"""
        if args.NMAXRT_FR is not None:
            self.model.crop.npk_crop.demand_uptake.NMAXRT_FR = args.NMAXRT_FR   
        """Maximum P concentration in roots as fraction of maximum P concentration in leaves"""
        if args.PMAXRT_FR is not None:
            self.model.crop.npk_crop.demand_uptake.PMAXRT_FR = args.PMAXRT_FR    
        """Maximum K concentration in roots as fraction  of maximum K concentration in leaves"""
        if args.KMAXRT_FR is not None:
            self.model.crop.npk_crop.demand_uptake.KMAXRT_FR = args.KMAXRT_FR    
        """Maximum N concentration in stems as fraction of maximum N concentration in leaves"""
        if args.NMAXST_FR is not None:
            self.model.crop.npk_crop.demand_uptake.NMAXST_FR = args.NMAXST_FR    
        """Maximum P concentration in stems as fraction of maximum P concentration in leaves"""
        if args.PMAXST_FR is not None:
            self.model.crop.npk_crop.demand_uptake.PMAXST_FR = args.PMAXST_FR    
        """Maximum K concentration in stems as fraction of maximum K concentration in leaves"""
        if args.KMAXST_FR is not None:
            self.model.crop.npk_crop.demand_uptake.KMAXST_FR = args.KMAXST_FR    
        """ Maximum N concentration in storage organs (kg N / kg dry biomass)"""
        if args.NMAXSO is not None:
            self.model.crop.npk_crop.demand_uptake.NMAXSO = args.NMAXSO    
        """Maximum P concentration in storage organs (kg P / kg dry biomass)"""
        if args.PMAXSO is not None:  
            self.model.crop.npk_crop.demand_uptake.PMAXSO = args.PMAXSO
        """Maximum K concentration in storage organs (kg K / kg dry biomass)""" 
        if args.KMAXSO is not None:         
            self.model.crop.npk_crop.demand_uptake.KMAXSO = args.KMAXSO    
        """Critical N concentration as fraction of maximum N concentration for vegetative
                        plant organs as a whole (leaves + stems)"""
        if args.NCRIT_FR is not None:
            self.model.crop.npk_crop.demand_uptake.NCRIT_FR = args.NCRIT_FR     
        """Critical P concentration as fraction of maximum P concentration for vegetative
                        plant organs as a whole (leaves + stems)"""
        if args.PCRIT_FR is not None:
            self.model.crop.npk_crop.demand_uptake.PCRIT_FR = args.PCRIT_FR      
        """Critical K concentration as fraction of maximum K concentration for vegetative
                        plant organs as a whole (leaves + stems)"""
        if args.KCRIT_FR is not None:
            self.model.crop.npk_crop.demand_uptake.KCRIT_FR = args.KCRIT_FR      
        
        """Time coefficient for N translation to storage organs (days)"""
        if args.TCNT is not None:
            self.model.crop.npk_crop.demand_uptake.TCNT = args.TCNT         
        """Time coefficient for P translation to storage organs (days)"""
        if args.TCPT is not None:
            self.model.crop.npk_crop.demand_uptake.TCPT = args.TCPT         
        """Time coefficient for K translation to storage organs (days)"""
        if args.TCKT is not None:
            self.model.crop.npk_crop.demand_uptake.TCKT = args.TCKT         
        """fraction of crop nitrogen uptake by biological fixation (kg N / kg dry biomass)"""
        if args.NFIX_FR is not None:
            self.model.crop.npk_crop.demand_uptake.NFIX_FR = args.NFIX_FR      
        """Maximum rate of N uptake (kg N / ha day)"""
        if args.RNUPTAKEMAX is not None:
            self.model.crop.npk_crop.demand_uptake.RNUPTAKEMAX = args.RNUPTAKEMAX 
        """Maximum rate of P uptake (kg P / ha day)"""
        if args.RPUPTAKEMAX is not None:
            self.model.crop.npk_crop.demand_uptake.RPUPTAKEMAX = args.RPUPTAKEMAX 
        """Maximum rate of K uptake (kg K / ha day)"""
        if args.RKUPTAKEMAX is not None:
            self.model.crop.npk_crop.demand_uptake.RKUPTAKEMAX = args.RKUPTAKEMAX        

        # NPK Stress Parameters
        """Maximum N concentration in leaves as function of DVS (kg N kg-1 dry biomass)"""
        if args.NMAXLV_TB is not None:
            self.model.crop.npk_stress.params.NMAXLV_TB = args.NMAXLV_TB    
        """Maximum P concentration in leaves as function of DVS (kg N / kg dry biomass)"""
        if args.PMAXLV_TB is not None:
            self.model.crop.npk_stress.params.PMAXLV_TB = args.PMAXLV_TB    
        """Maximum K concentration in leaves as function of DVS (kg N / kg dry biomass)"""
        if args.KMAXLV_TB is not None:
            self.model.crop.npk_stress.params.KMAXLV_TB = args.KMAXLV_TB    
        """Maximum N concentration in roots as fraction of maximum N concentration in leaves"""
        if args.NMAXRT_FR is not None:
            self.model.crop.npk_stress.params.NMAXRT_FR = args.NMAXRT_FR    
        """Maximum P concentration in roots as fraction of maximum P concentration in leaves"""
        if args.PMAXRT_FR is not None:
            self.model.crop.npk_stress.params.PMAXRT_FR = args.PMAXRT_FR    
        """Maximum K concentration in roots as fraction of maximum K concentration in leaves"""
        if args.KMAXRT_FR is not None:
            self.model.crop.npk_stress.params.KMAXRT_FR = args.KMAXRT_FR    
        """Maximum N concentration in stems as fraction of maximum N concentration in leaves"""
        if args.NMAXST_FR is not None:
            self.model.crop.npk_stress.params.NMAXST_FR = args.NMAXST_FR    
        """Maximum P concentration in stems as fraction of maximum P concentration in leaves"""
        if args.PMAXST_FR is not None:
            self.model.crop.npk_stress.params.PMAXST_FR = args.PMAXST_FR    
        """Maximum K concentration in stems as fraction of maximum K concentration in leaves"""
        if args.KMAXST_FR is not None:
            self.model.crop.npk_stress.params.KMAXST_FR = args.KMAXST_FR 
        """Critical N concentration as fraction of maximum N concentration for vegetative
                        plant organs as a whole (leaves + stems)"""
        if args.NCRIT_FR is not None:
            self.model.crop.npk_stress.params.NCRIT_FR = args.NCRIT_FR     
        """Critical P concentration as fraction of maximum P concentration for vegetative
                        plant organs as a whole (leaves + stems)"""
        if args.PCRIT_FR is not None:
            self.model.crop.npk_stress.params.PCRIT_FR = args.PCRIT_FR     
        """Critical K concentration as fraction of maximum L concentration for 
        vegetative plant organs as a whole (leaves + stems)"""
        if args.KCRIT_FR is not None:
            self.model.crop.npk_stress.params.KCRIT_FR = args.KCRIT_FR     
        """Residual N fraction in leaves (kg N / kg dry biomass)"""
        if args.NRESIDLV is not None:
            self.model.crop.npk_stress.params.NRESIDLV = args.NRESIDLV
        """Residual P fraction in leaves (kg P / kg dry biomass)"""
        if args.PRESIDLV is not None:
            self.model.crop.npk_stress.params.PRESIDLV = args.PRESIDLV
        """Residual K fraction in leaves (kg K / kg dry biomass)"""
        if args.KRESIDLV is not None:
            self.model.crop.npk_stress.params.KRESIDLV = args.KRESIDLV                    
        """Residual N fraction in stems (kg N / kg dry biomass)"""
        if args.NRESIDST is not None:
            self.model.crop.npk_stress.params.NRESIDST = args.NRESIDST 
        """Residual P fraction in stems (kg P/ kg dry biomass)"""
        if args.PRESIDST is not None:
            self.model.crop.npk_stress.params.PRESIDST = args.PRESIDST
        """Residual K fraction in stems (kg K/ kg dry biomass)"""
        if args.KRESIDST is not None:
            self.model.crop.npk_stress.params.KRESIDST = args.KRESIDST                
        """Coefficient for the reduction of RUE due to nutrient (N-P-K) stress"""
        if args.NLUE_NPK is not None:
            self.model.crop.npk_stress.params.NLUE_NPK = args.NLUE_NPK
    
        # NPK Translocation Parameters
        """Residual N fraction in leaves (kg N / kg dry biomass)""" 
        if args.NRESIDLV is not None:
            self.model.crop.npk_crop.translocation.NRESIDLV = args.NRESIDLV
        """Residual P fraction in leaves (kg P / kg dry biomass)""" 
        if args.PRESIDLV is not None:
            self.model.crop.npk_crop.translocation.PRESIDLV = args.PRESIDLV
        """Residual K fraction in leaves (kg K / kg dry biomass)"""
        if args.KRESIDLV is not None: 
            self.model.crop.npk_crop.translocation.KRESIDLV = args.KRESIDLV  
        """Residual N fraction in stems (kg N / kg dry biomass)""" 
        if args.NRESIDST is not None:
            self.model.crop.npk_crop.translocation.NRESIDST = args.NRESIDST
        """Residual K fraction in stems (kg P / kg dry biomass)"""
        if args.PRESIDST is not None: 
            self.model.crop.npk_crop.translocation.PRESIDST = args.PRESIDST
        """Residual P fraction in stems (kg K / kg dry biomass)"""
        if args.KRESIDST is not None: 
            self.model.crop.npk_crop.translocation.KRESIDST = args.KRESIDST        
        """NPK translocation from roots as a fraction of resp. total NPK amounts translocated
                            from leaves and stems"""
        if args.NPK_TRANSLRT_FR is not None:
            self.model.crop.npk_crop.translocation.NPK_TRANSLRT_FR = args.NPK_TRANSLRT_FR

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
        self.model = pcse.models.Wofost80(self.parameterprovider, self.weatherdataprovider,
                                         self.agromanagement, config=self.config)
        self._set_params(self.args)
        
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
