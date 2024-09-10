# -*- coding: utf-8 -*-
# Copyright (c) 2004-2014 Alterra, Wageningen-UR
# Allard de Wit (allard.dewit@wur.nl), April 2014

from ..utils.traitlets import Float
from ..utils import signals
from ..util import AfgenTrait, limit
from ..utils.decorators import prepare_rates, prepare_states
from ..base import ParamTemplate, StatesTemplate, RatesTemplate, \
    SimulationObject

class WOFOST_Storage_Organ_Dynamics(SimulationObject):
    """Implementation of storage organ dynamics.
    
    Storage organs are the most simple component of the plant in WOFOST and
    consist of a static pool of biomass. Growth of the storage organs is the
    result of assimilate partitioning. Death of storage organs is not
    implemented and the corresponding rate variable (DRSO) is always set to
    zero.
    
    Pods are green elements of the plant canopy and can as such contribute
    to the total photosynthetic active area. This is expressed as the Pod
    Area Index which is obtained by multiplying pod biomass with a fixed
    Specific Pod Area (SPA).

    **Simulation parameters**
    
    =======  ============================================= =======  ============
     Name     Description                                   Type     Unit
    =======  ============================================= =======  ============
    TDWI     Initial total crop dry weight                  SCr      |kg ha-1|
    RDRSOB   Relative Death rate of storage organs as a     Scr      |kg ha-1|
            function of development stage               
    SPA      Specific Pod Area                              SCr      |ha kg-1|
    =======  ============================================= =======  ============    

    **State variables**

    =======  ================================================= ==== ============
     Name     Description                                      Pbl      Unit
    =======  ================================================= ==== ============
    PAI      Pod Area Index                                     Y     -
    WSO      Weight of living storage organs                    Y     |kg ha-1|
    DWSO     Weight of dead storage organs                      N     |kg ha-1|
    TWSO     Total weight of storage organs                     Y     |kg ha-1|
    HWSO     Harvestable weight of storage organs               Y     |kg ha-1|
    LHW      Last Harvest weight of storage organs              Y     |kg ha-1|
    =======  ================================================= ==== ============

    **Rate variables**

    =======  ================================================= ==== ============
     Name     Description                                      Pbl      Unit
    =======  ================================================= ==== ============
    GRSO     Growth rate storage organs                         N   |kg ha-1 d-1|
    DRSO     Death rate storage organs                          N   |kg ha-1 d-1|
    DHSO     Death rate of harvestablestorage organs            N   |kg ha-1 d-1|
    GWSO     Net change in storage organ biomass                N   |kg ha-1 d-1|
    =======  ================================================= ==== ============
    
    **Signals send or handled**
    
    None
    
    **External dependencies**
    
    =======  =================================== =================  ============
     Name     Description                         Provided by         Unit
    =======  =================================== =================  ============
    ADMI     Above-ground dry matter             CropSimulation     |kg ha-1 d-1|
             increase
    FO       Fraction biomass to storage organs  DVS_Partitioning    - 
    FR       Fraction biomass to roots           DVS_Partitioning    - 
    =======  =================================== =================  ============
    """

    class Parameters(ParamTemplate):      
        SPA    = Float(-99.)
        TDWI   = Float(-99.)
        RDRSOB = AfgenTrait()

    class StateVariables(StatesTemplate):
        WSO  = Float(-99.) # Weight living storage organs
        DWSO = Float(-99.) # Weight dead storage organs
        TWSO = Float(-99.) # Total weight storage organs
        HWSO = Float(-99.) # Harvestable weight of storage organs
        PAI  = Float(-99.) # Pod Area Index
        LHW  = Float(-99.) # Last Harvest weight of storage organs

    class RateVariables(RatesTemplate):
        GRSO = Float(-99.)
        DRSO = Float(-99.)
        GWSO = Float(-99.)
        DHSO = Float(-99.)
        
    def initialize(self, day, kiosk, parvalues):
        """
        :param day: start date of the simulation
        :param kiosk: variable kiosk of this PCSE  instance
        :param parvalues: `ParameterProvider` object providing parameters as
                key/value pairs
        """

        self.params = self.Parameters(parvalues)
        self.kiosk = kiosk
        
        self._connect_signal(self._on_CROP_HARVEST, signal=signals.crop_harvest)

        # INITIAL STATES
        params = self.params
        # Initial storage organ biomass
        FO = self.kiosk["FO"]
        FR = self.kiosk["FR"]
        WSO  = (params.TDWI * (1-FR)) * FO
        DWSO = 0.
        HWSO = 0.
        LHW = HWSO
        TWSO = WSO + DWSO
        # Initial Pod Area Index
        PAI = WSO * params.SPA

        self.states = self.StateVariables(kiosk, publish=["WSO", "DWSO", "TWSO", 
                                                          "HWSO", "PAI", "LHW"],
                                          WSO=WSO, DWSO=DWSO, TWSO=TWSO, HWSO=HWSO,
                                          PAI=PAI, LHW=LHW)
        
        self.rates = self.RateVariables(kiosk, publish=[ "GRSO", "DRSO", "GWSO", "DHSO"])

    @prepare_rates
    def calc_rates(self, day, drv):
        rates  = self.rates
        states = self.states
        params = self.params
        k = self.kiosk
        
        FO = self.kiosk["FO"]
        ADMI = self.kiosk["ADMI"]

        # Growth/death rate organs
        rates.GRSO = ADMI * FO

        rates.DRSO = states.WSO * params.RDRSOB(k.DVS)
        rates.DHSO = states.HWSO * params.RDRSOB(k.DVS)
        rates.GWSO = rates.GRSO - rates.DRSO

    @prepare_states
    def integrate(self, day, delt=1.0):
        params = self.params
        rates = self.rates
        states = self.states

        # Stem biomass (living, dead, total)
        states.WSO += rates.GWSO
        states.HWSO += rates.GRSO - rates.DHSO
        states.DWSO += rates.DRSO
        states.TWSO = states.WSO + states.DWSO
        
        states.HWSO = limit(0, states.WSO, states.HWSO)
        # Calculate Pod Area Index (SAI)
        states.PAI = states.WSO * params.SPA

    # When the crop is harvested, reset harvestable crop dry matter
    def _on_CROP_HARVEST(self, day, efficiency=1.0):
        self.states.LHW = (efficiency) * self.states.HWSO
        self.states.HWSO = (1-efficiency) * self.states.HWSO