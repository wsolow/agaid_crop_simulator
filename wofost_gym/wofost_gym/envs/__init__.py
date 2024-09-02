from wofost_gym.envs.wofost_envs import NPK_Env
from wofost_gym.envs.wofost_envs import PP_Env
from wofost_gym.envs.wofost_envs import Limited_NPK_Env
from wofost_gym.envs.wofost_envs import Limited_N_Env
from wofost_gym.envs.wofost_envs import Limited_NW_Env
from wofost_gym.envs.wofost_envs import Limited_W_Env


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
            self.model.crop.npk_crop_dynamics.demand_uptake.params.NMAXLV_TB = args.NMAXLV_TB    
        """Maximum P concentration in leaves as function of DVS (kg P / kg dry biomass)"""
        if args.NMAXLV_TB is not None:
            self.model.crop.npk_crop_dynamics.demand_uptake.params.NMAXLV_TB  = args.NMAXLV_TB  
        """Maximum K concentration in leaves as function of DVS (kg K / kg dry biomass)"""
        if args.KMAXLV_TB is not None:
            self.model.crop.npk_crop_dynamics.demand_uptake.params.KMAXLV_TB = args.KMAXLV_TB    
        """ Maximum N concentration in roots as fraction of maximum N concentration in leaves"""
        if args.NMAXRT_FR is not None:
            self.model.crop.npk_crop_dynamics.demand_uptake.params.NMAXRT_FR = args.NMAXRT_FR   
        """Maximum P concentration in roots as fraction of maximum P concentration in leaves"""
        if args.PMAXRT_FR is not None:
            self.model.crop.npk_crop_dynamics.demand_uptake.params.PMAXRT_FR = args.PMAXRT_FR    
        """Maximum K concentration in roots as fraction  of maximum K concentration in leaves"""
        if args.KMAXRT_FR is not None:
            self.model.crop.npk_crop_dynamics.demand_uptake.params.KMAXRT_FR = args.KMAXRT_FR    
        """Maximum N concentration in stems as fraction of maximum N concentration in leaves"""
        if args.NMAXST_FR is not None:
            self.model.crop.npk_crop_dynamics.demand_uptake.params.NMAXST_FR = args.NMAXST_FR    
        """Maximum P concentration in stems as fraction of maximum P concentration in leaves"""
        if args.PMAXST_FR is not None:
            self.model.crop.npk_crop_dynamics.demand_uptake.params.PMAXST_FR = args.PMAXST_FR    
        """Maximum K concentration in stems as fraction of maximum K concentration in leaves"""
        if args.KMAXST_FR is not None:
            self.model.crop.npk_crop_dynamics.demand_uptake.params.KMAXST_FR = args.KMAXST_FR    
        """ Maximum N concentration in storage organs (kg N / kg dry biomass)"""
        if args.NMAXSO is not None:
            self.model.crop.npk_crop_dynamics.demand_uptake.params.NMAXSO = args.NMAXSO    
        """Maximum P concentration in storage organs (kg P / kg dry biomass)"""
        if args.PMAXSO is not None:  
            self.model.crop.npk_crop_dynamics.demand_uptake.params.PMAXSO = args.PMAXSO
        """Maximum K concentration in storage organs (kg K / kg dry biomass)""" 
        if args.KMAXSO is not None:         
            self.model.crop.npk_crop_dynamics.demand_uptake.params.KMAXSO = args.KMAXSO    
        """Critical N concentration as fraction of maximum N concentration for vegetative
                        plant organs as a whole (leaves + stems)"""
        if args.NCRIT_FR is not None:
            self.model.crop.npk_crop_dynamics.demand_uptake.params.NCRIT_FR = args.NCRIT_FR     
        """Critical P concentration as fraction of maximum P concentration for vegetative
                        plant organs as a whole (leaves + stems)"""
        if args.PCRIT_FR is not None:
            self.model.crop.npk_crop_dynamics.demand_uptake.params.PCRIT_FR = args.PCRIT_FR      
        """Critical K concentration as fraction of maximum K concentration for vegetative
                        plant organs as a whole (leaves + stems)"""
        if args.KCRIT_FR is not None:
            self.model.crop.npk_crop_dynamics.demand_uptake.params.KCRIT_FR = args.KCRIT_FR      
        
        """Time coefficient for N translation to storage organs (days)"""
        if args.TCNT is not None:
            self.model.crop.npk_crop_dynamics.demand_uptake.params.TCNT = args.TCNT         
        """Time coefficient for P translation to storage organs (days)"""
        if args.TCPT is not None:
            self.model.crop.npk_crop_dynamics.demand_uptake.params.TCPT = args.TCPT         
        """Time coefficient for K translation to storage organs (days)"""
        if args.TCKT is not None:
            self.model.crop.npk_crop_dynamics.demand_uptake.params.TCKT = args.TCKT         
        """fraction of crop nitrogen uptake by biological fixation (kg N / kg dry biomass)"""
        if args.NFIX_FR is not None:
            self.model.crop.npk_crop_dynamics.demand_uptake.params.NFIX_FR = args.NFIX_FR      
        """Maximum rate of N uptake (kg N / ha day)"""
        if args.RNUPTAKEMAX is not None:
            self.model.crop.npk_crop_dynamics.demand_uptake.params.RNUPTAKEMAX = args.RNUPTAKEMAX 
        """Maximum rate of P uptake (kg P / ha day)"""
        if args.RPUPTAKEMAX is not None:
            self.model.crop.npk_crop_dynamics.demand_uptake.params.RPUPTAKEMAX = args.RPUPTAKEMAX 
        """Maximum rate of K uptake (kg K / ha day)"""
        if args.RKUPTAKEMAX is not None:
            self.model.crop.npk_crop_dynamics.demand_uptake.params.RKUPTAKEMAX = args.RKUPTAKEMAX        

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
            self.model.crop.npk_crop_dynamics.translocation.params.NRESIDLV = args.NRESIDLV
        """Residual P fraction in leaves (kg P / kg dry biomass)""" 
        if args.PRESIDLV is not None:
            self.model.crop.npk_crop_dynamics.translocation.params.PRESIDLV = args.PRESIDLV
        """Residual K fraction in leaves (kg K / kg dry biomass)"""
        if args.KRESIDLV is not None: 
            self.model.crop.npk_crop_dynamics.translocation.params.KRESIDLV = args.KRESIDLV  
        """Residual N fraction in stems (kg N / kg dry biomass)""" 
        if args.NRESIDST is not None:
            self.model.crop.npk_crop_dynamics.translocation.params.NRESIDST = args.NRESIDST
        """Residual K fraction in stems (kg P / kg dry biomass)"""
        if args.PRESIDST is not None: 
            self.model.crop.npk_crop_dynamics.translocation.params.PRESIDST = args.PRESIDST
        """Residual P fraction in stems (kg K / kg dry biomass)"""
        if args.KRESIDST is not None: 
            self.model.crop.npk_crop_dynamics.translocation.params.KRESIDST = args.KRESIDST        
        """NPK translocation from roots as a fraction of resp. total NPK amounts translocated
                            from leaves and stems"""
        if args.NPK_TRANSLRT_FR is not None:
            self.model.crop.npk_crop_dynamics.translocation.params.NPK_TRANSLRT_FR = args.NPK_TRANSLRT_FR
