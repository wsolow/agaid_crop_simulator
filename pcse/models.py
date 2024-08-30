# -*- coding: utf-8 -*-
# Copyright (c) 2004-2014 Alterra, Wageningen-UR
# Allard de Wit (allard.dewit@wur.nl), April 2014
# Modified by Will Solow, 2024

from .engine import Engine


class Wofost80(Engine):
    """Convenience class for running WOFOST8.0 nutrient and water-limited production

    :param parameterprovider: A ParameterProvider instance providing all parameter values
    :param weatherdataprovider: A WeatherDataProvider object
    :param agromanagement: Agromanagement data
    """
    #
    # config = "Wofost80_NWLP_FD.conf"

    def __init__(self, parameterprovider, weatherdataprovider, agromanagement, config):
        Engine.__init__(self, parameterprovider, weatherdataprovider, agromanagement,
                        config=config)
