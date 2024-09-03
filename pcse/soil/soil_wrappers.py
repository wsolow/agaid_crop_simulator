# -*- coding: utf-8 -*-
# Copyright (c) 2004-2020 Alterra, Wageningen-UR
# Allard de Wit (allard.dewit@wur.nl), September 2020
# Modified by Will Solow, 2024
"""This module wraps the soil components for water and nutrients so that they run jointly
within the same model.
"""
from ..base import SimulationObject
from .classic_waterbalance import WaterbalanceFD
from .classic_waterbalance import WaterbalancePP
from .npk_soil_dynamics import NPK_Soil_Dynamics
from .npk_soil_dynamics import NPK_Soil_Dynamics_PP
from .npk_soil_dynamics import NPK_Soil_Dynamics_LN
from ..utils.traitlets import Instance


class SoilModuleWrapper_LNPKW(SimulationObject):
    """This wraps the soil water balance for free drainage conditions and NPK balance
    for production conditions limited by both soil water and NPK.
    """
    WaterbalanceFD = Instance(SimulationObject)
    NPK_Soil_Dynamics = Instance(SimulationObject)

    def initialize(self, day, kiosk, parvalues):
        """
        :param day: start date of the simulation
        :param kiosk: variable kiosk of this PCSE instance
        :param parvalues: dictionary with parameter key/value pairs
        """
        self.WaterbalanceFD = WaterbalanceFD(day, kiosk, parvalues)
        self.NPK_Soil_Dynamics = NPK_Soil_Dynamics(day, kiosk, parvalues)

    def calc_rates(self, day, drv):
        self.WaterbalanceFD.calc_rates(day, drv)
        self.NPK_Soil_Dynamics.calc_rates(day, drv)

    def integrate(self, day, delt=1.0):
        self.WaterbalanceFD.integrate(day, delt)
        self.NPK_Soil_Dynamics.integrate(day, delt)

class SoilModuleWrapper_PP(SimulationObject):

    """This wraps the soil water balance for free drainage conditions and NPK balance
    for potential production with unlimited water and NPK.
    """
    WaterbalanceFD = Instance(SimulationObject)
    NPK_Soil_Dynamics = Instance(SimulationObject)

    def initialize(self, day, kiosk, parvalues):
        """
        :param day: start date of the simulation
        :param kiosk: variable kiosk of this PCSE instance
        :param parvalues: dictionary with parameter key/value pairs
        """
        self.WaterbalanceFD = WaterbalancePP(day, kiosk, parvalues)
        self.NPK_Soil_Dynamics = NPK_Soil_Dynamics_PP(day, kiosk, parvalues)

    def calc_rates(self, day, drv):
        self.WaterbalanceFD.calc_rates(day, drv)
        self.NPK_Soil_Dynamics.calc_rates(day, drv)

    def integrate(self, day, delt=1.0):
        self.WaterbalanceFD.integrate(day, delt)
        self.NPK_Soil_Dynamics.integrate(day, delt)

class SoilModuleWrapper_LW(SimulationObject):

    """This wraps the soil water balance for free drainage conditions and NPK balance
    for production conditions limited by soil water.
    """
    WaterbalanceFD = Instance(SimulationObject)
    NPK_Soil_Dynamics = Instance(SimulationObject)

    def initialize(self, day, kiosk, parvalues):
        """
        :param day: start date of the simulation
        :param kiosk: variable kiosk of this PCSE instance
        :param parvalues: dictionary with parameter key/value pairs
        """
        self.WaterbalanceFD = WaterbalanceFD(day, kiosk, parvalues)
        self.NPK_Soil_Dynamics = NPK_Soil_Dynamics_PP(day, kiosk, parvalues)

    def calc_rates(self, day, drv):
        self.WaterbalanceFD.calc_rates(day, drv)
        self.NPK_Soil_Dynamics.calc_rates(day, drv)

    def integrate(self, day, delt=1.0):
        self.WaterbalanceFD.integrate(day, delt)
        self.NPK_Soil_Dynamics.integrate(day, delt)

class SoilModuleWrapper_LNW(SimulationObject):

    """This wraps the soil water balance for free drainage conditions and NPK balance
    for production conditions limited by both soil water and N, but assumes abundance
    of P/K.
    """
    WaterbalanceFD = Instance(SimulationObject)
    NPK_Soil_Dynamics = Instance(SimulationObject)

    def initialize(self, day, kiosk, parvalues):
        """
        :param day: start date of the simulation
        :param kiosk: variable kiosk of this PCSE instance
        :param parvalues: dictionary with parameter key/value pairs
        """
        self.WaterbalanceFD = WaterbalanceFD(day, kiosk, parvalues)
        self.NPK_Soil_Dynamics = NPK_Soil_Dynamics_LN(day, kiosk, parvalues)

    def calc_rates(self, day, drv):
        self.WaterbalanceFD.calc_rates(day, drv)
        self.NPK_Soil_Dynamics.calc_rates(day, drv)

    def integrate(self, day, delt=1.0):
        self.WaterbalanceFD.integrate(day, delt)
        self.NPK_Soil_Dynamics.integrate(day, delt)

class SoilModuleWrapper_LNPK(SimulationObject):

    """This wraps the soil water balance for free drainage conditions and NPK balance
    for production conditions limited by NPK but assumes abundant water.
    """
    WaterbalanceFD = Instance(SimulationObject)
    NPK_Soil_Dynamics = Instance(SimulationObject)

    def initialize(self, day, kiosk, parvalues):
        """
        :param day: start date of the simulation
        :param kiosk: variable kiosk of this PCSE instance
        :param parvalues: dictionary with parameter key/value pairs
        """
        self.WaterbalanceFD = WaterbalancePP(day, kiosk, parvalues)
        self.NPK_Soil_Dynamics = NPK_Soil_Dynamics(day, kiosk, parvalues)

    def calc_rates(self, day, drv):
        self.WaterbalanceFD.calc_rates(day, drv)
        self.NPK_Soil_Dynamics.calc_rates(day, drv)

    def integrate(self, day, delt=1.0):
        self.WaterbalanceFD.integrate(day, delt)
        self.NPK_Soil_Dynamics.integrate(day, delt)

class SoilModuleWrapper_LN(SimulationObject):

    """This wraps the soil water balance for free drainage conditions and NPK balance
    for production conditions limited by Nitrogen, but assumes abundance of P/K
    and water.
    """
    WaterbalanceFD = Instance(SimulationObject)
    NPK_Soil_Dynamics = Instance(SimulationObject)

    def initialize(self, day, kiosk, parvalues):
        """
        :param day: start date of the simulation
        :param kiosk: variable kiosk of this PCSE instance
        :param parvalues: dictionary with parameter key/value pairs
        """
        self.WaterbalanceFD = WaterbalancePP(day, kiosk, parvalues)
        self.NPK_Soil_Dynamics = NPK_Soil_Dynamics_LN(day, kiosk, parvalues)

    def calc_rates(self, day, drv):
        self.WaterbalanceFD.calc_rates(day, drv)
        self.NPK_Soil_Dynamics.calc_rates(day, drv)

    def integrate(self, day, delt=1.0):
        self.WaterbalanceFD.integrate(day, delt)
        self.NPK_Soil_Dynamics.integrate(day, delt)








        