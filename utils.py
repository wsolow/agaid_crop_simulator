from dataclasses import dataclass, field
from pathlib import Path
import wofost_gym.wrappers.wrappers as wrappers
import typing
import gymnasium as gym
import warnings
from inspect import getmembers, isfunction

warnings.filterwarnings("ignore", category=UserWarning)

# Configuration parameters for the WOFOST model - to be used only if 
# making a new configuration file is not desired
@dataclass
class WOFOST_Args:
    # All editable parameters for the WOFOST crop and soil. If left to default
    # of None, values will be drawn from the .yaml files in /env_config/
    # NPK Soil dynamics params
    """Base soil supply of N available through mineralization kg/ha"""
    NSOILBASE: float = None   
    """Fraction of base soil N that comes available every day"""         
    NSOILBASE_FR: float = None 
    """Base soil supply of P available through mineralization kg/ha"""
    PSOILBASE: float = None   
    """Fraction of base soil P that comes available every day"""         
    PSOILBASE_FR: float = None 
    """Base soil supply of K available through mineralization kg/ha"""
    KSOILBASE: float = None   
    """Fraction of base soil K that comes available every day"""         
    KSOILBASE_FR: float = None 
    """Initial N available in the N pool (kg/ha)"""
    NAVAILI: float = None
    """Initial P available in the P pool (kg/ha)"""
    PAVAILI: float = None
    """Initial K available in the K pool (kg/ha)"""
    KAVAILI: float = None
    """Background supply of N through atmospheric deposition (kg/ha/day)"""
    BG_N_SUPPLY: float = None
    """Background supply of P through atmospheric deposition (kg/ha/day)"""
    BG_P_SUPPLY: float = None
    """Background supply of K through atmospheric deposition (kg/ha/day)"""
    BG_K_SUPPLY: float = None

    # Waterbalance soil dynamics params
    """Field capacity of the soil"""
    SMFCF: float = None                  
    """Porosity of the soil"""
    SM0: float = None                                
    """Wilting point of the soil"""
    SMW: float = None                          
    """Soil critical air content (waterlogging)"""
    CRAIRC: float = None       
    """maximum percolation rate root zone (cm/day)"""
    SOPE: float = None    
    """maximum percolation rate subsoil (cm/day)"""
    KSUB: float = None                  
    """Soil rootable depth (cm)"""
    RDMSOL: float = None                            
    """Indicates whether non-infiltrating fraction of rain is a function of storm size (1) or not (0)"""
    IFUNRN: bool = None    
    """Maximum surface storage (cm)"""                               
    SSMAX: float = None                          
    """Initial surface storage (cm)"""
    SSI: float = None                   
    """Initial amount of water in total soil profile (cm)"""
    WAV: float = None 
    """Maximum fraction of rain not-infiltrating into the soil"""
    NOTINF: float = None
    """Initial maximum moisture content in initial rooting depth zone"""
    SMLIM: float = None  
    """CO2 in atmosphere (ppm)"""
    CO2: float = None  


     # WOFOST Parameters
    """Conversion factor for assimilates to leaves"""
    CVL: float = None
    """Conversion factor for assimilates to storage organs"""
    CVO: float = None    
    """onversion factor for assimilates to roots"""  
    CVR: float = None     
    """Conversion factor for assimilates to stems"""
    CVS: float = None     

    # Assimilation Parameters
    """ Max leaf |CO2| assim. rate as a function of of DVS (kg/ha/hr)"""
    AMAXTB: float = None   
    """ Light use effic. single leaf as a function of daily mean temperature |kg ha-1 hr-1 /(J m-2 s-1)|"""
    EFFTB: float = None
    """Extinction coefficient for diffuse visible as function of DVS"""
    KDIFTB: float = None    
    """Reduction factor of AMAX as function of daily mean temperature"""
    TMPFTB: float = None
    """Reduction factor of AMAX as function of daily minimum temperature"""
    TMNFTB: float = None  
    """Correction factor for AMAX given atmospheric CO2 concentration.""" 
    CO2AMAXTB: float = None 
    """Correction factor for EFF given atmospheric CO2 concentration."""
    CO2EFFTB: float = None   

    # Evapotranspiration Parameters
    """Correction factor for potential transpiration rate"""
    CFET: float = None 
    """Dependency number for crop sensitivity to soil moisture stress."""  
    DEPNR: float = None   
    """Extinction coefficient for diffuse visible as function of DVS.""" 
    KDIFTB: float = None   
    """Switch oxygen stress on (1) or off (0)"""
    IOX: bool = None  
    """Switch airducts on (1) or off (0) """    
    IAIRDU: bool = None 
    """Reduction factor for TRAMX as function of atmospheric CO2 concentration"""      
    CO2TRATB: float = None
   
    # Leaf Dynamics Parameters
    """Maximum relative increase in LAI (ha / ha d)"""
    RGRLAI: float = None      
    """Life span of leaves growing at 35 Celsius (days)"""          
    SPAN: float = None   
    """Lower threshold temp for ageing of leaves (C)"""  
    TBASE: float = None  
    """Max relative death rate of leaves due to water stress"""  
    PERDL: float = None    
    """Extinction coefficient for diffuse visible light as function of DVS"""
    KDIFTB: float = None   
    """Specific leaf area as a function of DVS (ha/kg)"""
    SLATB: float = None  
    """Maximum relative death rate of leaves due to nutrient NPK stress"""  
    RDRNS: float = None    
    """coefficient for the reduction due to nutrient NPK stress of the LAI increas
            (during juvenile phase)"""
    NLAI: float = None    
    """Coefficient for the effect of nutrient NPK stress on SLA reduction""" 
    NSLA: float = None  
    """Max. relative death rate of leaves due to nutrient NPK stress"""   
    RDRN: float = None    
   
    # NPK Dynamics Parameters  
    """Maximum N concentration in leaves as function of DVS (kg N / kg dry biomass)"""
    NMAXLV_TB: float = None      
    """Maximum P concentration in leaves as function of DVS (kg P / kg dry biomass)"""
    PMAXLV_TB: float = None     
    """Maximum K concentration in leaves as function of DVS (kg K / kg dry biomass)"""
    KMAXLV_TB: float = None    
    """Maximum N concentration in roots as fraction of maximum N concentration in leaves"""
    NMAXRT_FR: float = None      
    """Maximum P concentration in roots as fraction of maximum P concentration in leaves"""
    PMAXRT_FR: float = None      
    """Maximum K concentration in roots as fraction of maximum K concentration in leaves"""
    KMAXRT_FR: float = None      
    """Maximum N concentration in stems as fraction of maximum N concentration in leaves"""
    NMAXST_FR: float = None      
    """Maximum P concentration in stems as fraction of maximum P concentration in leaves"""
    PMAXST_FR: float = None     
    """Maximum K concentration in stems as fraction of maximum K concentration in leaves"""
    KMAXST_FR: float = None   

    """Residual N fraction in leaves (kg N / kg dry biomass)""" 
    NRESIDLV: float = None 
    """Residual P fraction in leaves (kg P / kg dry biomass)""" 
    PRESIDLV: float = None
    """Residual K fraction in leaves (kg K / kg dry biomass)""" 
    KRESIDLV: float = None    
    """Residual N fraction in stems (kg N / kg dry biomass)""" 
    NRESIDST: float = None    
    """Residual K fraction in stems (kg P / kg dry biomass)""" 
    PRESIDST: float = None 
    """Residual P fraction in stems (kg K / kg dry biomass)""" 
    KRESIDST: float = None                 
    """NPK translocation from roots as a fraction of resp. total NPK amounts translocated
                        from leaves and stems"""     

    """Residual N fraction in roots (kg N / kg dry biomass)"""
    NRESIDRT: float = None                              
    """Residual P fraction in roots (kg P / kg dry biomass)"""
    PRESIDRT: float = None       
    """Residual K fraction in roots (kg K / kg dry biomass)"""
    KRESIDRT: float = None              

    # Partioning Parameters
    """Partitioning to roots as a function of development stage"""
    FRTB: float = None     
    """Partitioning to stems as a function of development stage"""
    FSTB: float = None     
    """Partitioning to leaves as a function of development stage"""
    FLTB: float = None     
    """Partitioning to starge organs as a function of development stage"""
    FOTB: float = None     
    """Coefficient for the effect of N stress on leaf biomass allocation"""
    NPART: float = None    
   
    # Vernalization Parameters
    """Saturated vernalisation requirements (days)"""
    VERNSAT: float = None
    """Base vernalisation requirements (days)"""
    VERNBASE: float = None
    """Rate of vernalisation as a function of daily mean temperature"""
    VERNRTB: float = None
    """Critical development stage after which the effect of vernalisation is halted"""
    VERNDVS: float = None

    # Phenology Parameters
    """Temperature sum from sowing to emergence (C day)"""
    TSUMEM: float = None   
    """Base temperature for emergence (C)"""
    TBASEM: float = None
    """Maximum effective temperature for emergence (C day)"""
    TEFFMX: float = None
    """Temperature sum from emergence to anthesis (C day)"""
    TSUM1: float = None
    """Temperature sum from anthesis to maturity (C day)"""
    TSUM2: float = None
    """Switch for phenological development options temperature only (IDSL=0), 
    including daylength (IDSL=1) and including vernalization (IDSL>=2)"""
    IDSL: float = None
    """Optimal daylength for phenological development (hr)"""
    DLO: float = None  
    """Critical daylength for phenological development (hr)"""
    DLC: float = None
    """Initial development stage at emergence. Usually this is zero, but it can 
    be higher or crops that are transplanted (e.g. paddy rice)"""
    DVSI: float = None
    """Final development stage"""
    DVSEND: float = None      
    """Daily increase in temperature sum as a function of daily mean temperature (C)"""               
    DTSMTB: float = None

    # Respiration Parameters
    """Relative increase in maintenance repiration rate with each 10 degrees increase in temperature"""
    Q10: float = None    
    """Relative maintenance respiration rate for roots |kg CH2O kg-1 d-1|"""
    RMR: float = None 
    """ Relative maintenance respiration rate for stems |kg CH2O kg-1 d-1| """   
    RMS: float = None 
    """Relative maintenance respiration rate for leaves |kg CH2O kg-1 d-1|""" 
    RML: float = None                                         
    """Relative maintenance respiration rate for storage organs |kg CH2O kg-1 d-1|"""
    RMO: float = None    

    # Root Dynamics Parameters
    """Initial rooting depth (cm)"""
    RDI: float = None
    """Daily increase in rooting depth  |cm day-1|"""
    RRI: float = None   
    """Maximum rooting depth of the crop (cm)""" 
    RDMCR: float = None
    """Maximum rooting depth of the soil (cm)"""
    RDMSOL: float = None
    """Presence of air ducts in the root (1) or not (0)""" 
    IAIRDU: bool = None
    """Relative death rate of roots as a function of development stage"""
    RDRRTB: float = None

    # Stem Dynamics Parameters   
    """Relative death rate of stems as a function of development stage"""
    RDRSTB: float = None   
    """Specific Stem Area as a function of development stage (ha/kg)"""
    SSATB: float = None   
   
    # Storage Organs Dynamics Parameters
    """Initial total crop dry weight (kg/ha)"""
    TDWI: float = None    
    """Specific Pod Area (ha / kg)""" 
    SPA: float = None    
    
    # NPK Demand Uptake Parameters     
    NMAXSO: float = None      
    """Maximum P concentration in storage organs (kg P / kg dry biomass)"""  
    PMAXSO: float = None 
    """Maximum K concentration in storage organs (kg K / kg dry biomass)"""          
    KMAXSO: float = None      
    """Critical N concentration as fraction of maximum N concentration for vegetative
                    plant organs as a whole (leaves + stems)"""
    NCRIT_FR: float = None       
    """Critical P concentration as fraction of maximum P concentration for vegetative
                    plant organs as a whole (leaves + stems)"""
    PCRIT_FR: float = None        
    """Critical K concentration as fraction of maximum K concentration for vegetative
                    plant organs as a whole (leaves + stems)"""
    KCRIT_FR: float = None        
    
    """Time coefficient for N translation to storage organs (days)"""
    TCNT: float = None           
    """Time coefficient for P translation to storage organs (days)"""
    TCPT: float = None           
    """Time coefficient for K translation to storage organs (days)"""
    TCKT: float = None           
    """fraction of crop nitrogen uptake by biological fixation (kg N / kg dry biomass)"""
    NFIX_FR: float = None        
    """Maximum rate of N uptake (kg N / ha day)"""
    RNUPTAKEMAX: float = None   
    """Maximum rate of P uptake (kg P / ha day)"""
    RPUPTAKEMAX: float = None   
    """Maximum rate of K uptake (kg K / ha day)"""
    RKUPTAKEMAX: float = None          

    # NPK Stress Parameters         
    NCRIT_FR: float = None       
    """Critical P concentration as fraction of maximum P concentration for vegetative
                    plant organs as a whole (leaves + stems)"""
    PCRIT_FR: float = None       
    """Critical K concentration as fraction of maximum L concentration for 
    vegetative plant organs as a whole (leaves + stems)"""
    KCRIT_FR: float = None                    
    """Coefficient for the reduction of RUE due to nutrient (N-P-K) stress"""
    NLUE_NPK: float = None 
   
    # NPK Translocation Parameters
    NPK_TRANSLRT_FR: float = None 

@dataclass
class NPK_Args:
    """Parameters for the WOFOST8 model"""
    """Best if modified in /env_config/ but can be modified here for small changes"""
    wf_args: WOFOST_Args

    """Location of data folder which contains multiple runs"""
    save_folder: str = "data/"

    """Environment ID"""
    env_id: str = "wofost-v0"
    """Env Reward Function"""
    env_reward: str = "default"
    """Environment seed"""
    seed: int = 0
    """Path"""
    path: str = "/Users/wsolow/Projects/agaid_crop_simulator/"
    """Path to policy if using a trained Deep RL Agent Policy"""
    """Typically in wandb/files/"""
    agent_path: str = None
    """Agent type (PPO, DQN, SAC)"""
    agent_type: str = None
    """Policy name if using a policy in the policies.py file"""
    policy_name: str = None

    """Output Variables"""
    """See env_config/README.md for more information"""
    output_vars: list = field(default_factory = lambda: ['DVS', 'TOTN', 'TOTP', 'TOTK', 'TOTIRRIG', 'LAI', 'RD', 'WSO','GWSO', 'NAVAIL', 'PAVAIL', 'KAVAIL', 'WC', 'SM'])
    """Weather Variables"""
    weather_vars: list = field(default_factory = lambda: ['IRRAD', 'TMIN', 'TMAX', 'TEMP', 'VAP', 'RAIN', 'WIND'])
    """Year range, incremented by 1"""
    year_range: list = field(default_factory = lambda: [1984, 2000])
    """Latitude Range, incremented by .5"""
    lat_range: list = field(default_factory = lambda: [50, 50])
    """Longitude Range of values, incremented by .5"""
    long_range: list = field(default_factory = lambda: [5, 5])

    """Intervention Interval"""
    intvn_interval: int = 1
    """Number of NPK Fertilization Actions"""
    """Total number of actions available will be 3*num_fert^3 + num_irrig"""
    num_fert: int = 2
    """Number of Irrgiation Actions"""
    num_irrig: int = 2

    """Maximum N applied in kg/ha (used in reward function)"""
    max_n: float = 20
    """Maximum K applied in kg/ha (used in reward function)"""
    max_p: float = 20
    """Maximum K applied in kg/ha (used in reward function)"""
    max_k: float = 20
    """Max water applied in cm (used in reward function)"""
    max_w: float = 20

    """Coefficient for Nitrogen Recovery after fertilization"""
    n_recovery: float = 0.7
    """Coefficient for Phosphorous Recovery after fertilization"""
    p_recovery: float = 0.7
    """Coefficient for Potassium Recovery after fertilization"""
    k_recovery: float = 0.7
    """Amount of fertilizer coefficient in kg/ha"""
    fert_amount: float = 2
    """Amount of water coefficient in cm/water"""
    irrig_amount: float  = 0.5
    """Coefficient for cost of fertilization"""
    beta: float = 10.0

    """Relative path to agromanagement configuration file"""
    agro_fpath: str = "env_config/agro_config/test_agro_npk.yaml"
    """Relative path to crop configuration file"""
    crop_fpath: str = "env_config/crop_config/"
    """Relative path to site configuration file"""
    site_fpath: str = "env_config/site_config/"

    """Flag for resetting to random year"""
    random_reset: bool = False

# Function to wrap the environment with a given reward function
# Based on the reward functions created in the wofost_gym/wrappers/
def wrap_env_reward(env: gym.Env, args):


    if args.env_reward == "default":
        print('Default Reward Function')
        return env
    elif args.env_reward == "fertilizationcost":
        print('Fertilization Cost Reward Function')
        return wrappers.RewardFertilizationCostWrapper(env)
    elif args.env_reward == 'fertilization_threshold':
        print('Fertilization Threshold Reward Function')
        return wrappers.RewardFertilizationThresholdWrapper(env)