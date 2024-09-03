# -*- coding: utf-8 -*-
# Copyright (c) 2004-2015 Alterra, Wageningen-UR
# Allard de Wit (allard.dewit@wur.nl), Juli 2015
# from __future__ import print_function
# Modified by Will Solow, 2024
"""Implementation of AgroManager and related classes for agromanagement actions in PCSE.

Available classes:

  * CropCalendar: A class for handling cropping calendars
  * TimedEventDispatcher: A class for handling timed events (e.g. events connected to a date)
  * StateEventDispatcher: A class for handling state events (e.g. events that happen when a state variable reaches
    a certain values.
  * AgroManager: A class for handling all agromanagement events which encapsulates
    the CropCalendar and Timed/State events.
"""

from datetime import date, timedelta
import logging

from .base import DispatcherObject, VariableKiosk, SimulationObject, ParameterProvider, AncillaryObject
from .traitlets import HasTraits, Float, Int, Instance, Enum, Bool, List, Dict, Unicode
from . import exceptions as exc
from .util import ConfigurationLoader
from . import signals
from . import exceptions as exc

def check_date_range(day, start, end):
    """returns True if start <= day < end

    Optionally, end may be None. in that case return True if start <= day

    :param day: the date that will be checked
    :param start: the start date of the range
    :param end: the end date of the range or None
    :return: True/False
    """

    if end is None:
        return start <= day
    else:
        return start <= day < end
        

def take_first(iterator):
    """Return the first item of the given iterator.
    """
    for item in iterator:
        return item

class CropCalendar(HasTraits, DispatcherObject):
    """A crop calendar for managing the crop cycle.

    A `CropCalendar` object is responsible for storing, checking, starting and ending
    the crop cycle. The crop calendar is initialized by providing the parameters needed
    for defining the crop cycle. At each time step the instance of `CropCalendar` is called
    and at dates defined by its parameters it initiates the appropriate actions:

    - sowing/emergence: A `crop_start` signal is dispatched including the parameters needed to
      start the new crop simulation object
    - maturity/harvest: the crop cycle is ended by dispatching a `crop_finish` signal with the
      appropriate parameters.

    :param kiosk: The PCSE VariableKiosk instance
    :param crop_name: String identifying the crop
    :param variety_name: String identifying the variety
    :param site_name: String identifying the site
    :param variation_name: String identifying the site variation
    :param crop_start_date: Start date of the crop simulation
    :param crop_start_type: Start type of the crop simulation ('sowing', 'emergence')
    :param crop_end_date: End date of the crop simulation
    :param crop_end_type: End type of the crop simulation ('harvest', 'maturity', 'earliest')
    :param max_duration: Integer describing the maximum duration of the crop cycle

    :return: A CropCalendar Instance
    """

    # Characteristics of the crop cycle
    crop_name = Unicode()
    variety_name = Unicode()
    site_name = Unicode()
    variation = Unicode()
    crop_start_date = Instance(date)
    crop_start_type = Enum(["sowing", "emergence"])
    crop_end_date = Instance(date)
    crop_end_type = Enum(["maturity", "harvest", "earliest"])
    max_duration = Int()

    # system parameters
    kiosk = Instance(VariableKiosk)
    parameterprovider = Instance(ParameterProvider)
    mconf = Instance(ConfigurationLoader)
    logger = Instance(logging.Logger)

    # Counter for duration of the crop cycle
    duration = Int(0)
    in_crop_cycle = Bool(False)

    def __init__(self, kiosk, crop_name=None, variety_name=None, site_name=None, 
                 variation_name= None, crop_start_date=None,
                 crop_start_type=None, crop_end_date=None, crop_end_type=None, max_duration=None):

        # set up logging
        loggername = "%s.%s" % (self.__class__.__module__,
                                self.__class__.__name__)

        self.logger = logging.getLogger(loggername)
        self.kiosk = kiosk
        self.crop_name = crop_name
        self.variety_name = variety_name
        self.site_name = site_name
        self.variation_name = variation_name
        self.crop_start_date = crop_start_date
        self.crop_start_type = crop_start_type
        self.crop_end_date = crop_end_date
        self.crop_end_type = crop_end_type
        self.max_duration = max_duration

        self._connect_signal(self._on_CROP_FINISH, signal=signals.crop_finish)

    def validate(self, campaign_start_date, next_campaign_start_date):
        """Validate the crop calendar internally and against the interval for
        the agricultural campaign.

        :param campaign_start_date: start date of this campaign
        :param next_campaign_start_date: start date of the next campaign
        """

        # Check that crop_start_date is before crop_end_date
        crop_end_date = self.crop_end_date
        if self.crop_end_type == "maturity":
            crop_end_date = self.crop_start_date + timedelta(days=self.max_duration)
        if self.crop_start_date >= crop_end_date:
            msg = "crop_end_date before or equal to crop_start_date for crop '%s'!"
            raise exc.PCSEError(msg % (self.crop_start_date, self.crop_end_date))

        # check that crop_start_date is within the campaign interval
        r = check_date_range(self.crop_start_date, campaign_start_date, next_campaign_start_date)
        if r is not True:
            msg = "Start date (%s) for crop '%s' vareity '%s' not within campaign window (%s - %s)." % \
                  (self.crop_start_date, self.crop_name, self.variety_name,
                   campaign_start_date, next_campaign_start_date)
            raise exc.PCSEError(msg)

    def __call__(self, day):
        """Runs the crop calendar to determine if any actions are needed.

        :param day:  a date object for the current simulation day
        :param drv: the driving variables at this day
        :return: None
        """

        if self.in_crop_cycle:
            self.duration += 1

        # Start of the crop cycle
        if day == self.crop_start_date:  # Start a new crop
            self.duration = 0
            self.in_crop_cycle = True
            msg = "Starting crop (%s) with variety (%s) on day %s" % (self.crop_name, self.variety_name, day)
            self.logger.info(msg)
            self._send_signal(signal=signals.crop_start, day=day, crop_name=self.crop_name,
                              variety_name=self.variety_name, site_name=self.site_name,
                              variation_name=self.variation_name, crop_start_type=self.crop_start_type,
                              crop_end_type=self.crop_end_type)

        # end of the crop cycle
        finish_type = None
        if self.in_crop_cycle:
            # Check if crop_end_date is reached for CROP_END_TYPE harvest/earliest
            if self.crop_end_type in ["harvest", "earliest"]:
                if day == self.crop_end_date:
                    finish_type = "harvest"

            # Check for forced stop because maximum duration is reached
            if self.in_crop_cycle and self.duration == self.max_duration:
                finish_type = "max_duration"

        # If finish condition is reached send a signal to finish the crop
        if finish_type is not None:
            self.in_crop_cycle = False
            self._send_signal(signal=signals.crop_finish, day=day,
                              finish_type=finish_type, crop_delete=True)

    def _on_CROP_FINISH(self):
        """Register that crop has reached the end of its cycle.
        """
        self.in_crop_cycle = False

    def get_end_date(self):
        """Return the end date of the crop cycle.

        This is either given as the harvest date or calculated as
        crop_start_date + max_duration

        :return: a date object
        """
        if self.crop_end_type in ["harvest", 'earliest']:
            return self.crop_end_date
        else:
            return self.crop_start_date + timedelta(days=self.max_duration)

    def get_start_date(self):
        """Returns the start date of the cycle. This is always self.crop_start_date

        :return: the start date
        """
        return self.crop_start_date

class AgroManager(AncillaryObject):
    """Class for continuous AgroManagement actions including crop rotations and events.

    See also the documentation for the classes `CropCalendar`, `TimedEventDispatcher` and `StateEventDispatcher`.

    The AgroManager takes care of executing agromanagent actions that typically occur on agricultural
    fields including planting and harvesting of the crop, as well as management actions such as fertilizer
    application, irrigation, mowing and spraying.

    The agromanagement during the simulation is implemented as a sequence of campaigns. Campaigns start on a
    prescribed calendar date and finalize when the next campaign starts. The simulation ends either explicitly by
    provided a trailing empty campaign or by deriving the end date from the crop calendar and timed events in the
    last campaign. See also the section below on `end_date` property.

    Each campaign is characterized by zero or one crop calendar, zero or more timed events and zero or more
    state events.
    The structure of the data needed as input for AgroManager is most easily understood with the example
    (in YAML) below. The definition consists of three campaigns, the first starting on 1999-08-01, the second
    starting on 2000-09-01 and the last campaign starting on 2001-03-01. The first campaign consists of a crop
    calendar for winter-wheat starting with sowing at the given crop_start_date. During the campaign there are
    timed events for irrigation at 2000-05-25 and 2000-06-30. Moreover, there are state events for  fertilizer
    application (event_signal: apply_npk) given by development stage (DVS) at DVS 0.3, 0.6 and 1.12.

    The second campaign has no crop calendar, timed events or state events. This means that this is a period of
    bare soil with only the water balance running. The third campaign is for fodder maize sown at 2001-04-15
    with two series of timed events (one for irrigation and one for N/P/K application) and no state events.
    The end date of the simulation in this case will be 2001-11-01 (2001-04-15 + 200 days).

    An example of an agromanagement definition file::

        AgroManagement:
        - 1999-08-01:
            CropCalendar:
                crop_name: wheat
                variety_name: winter-wheat
                crop_start_date: 1999-09-15
                crop_start_type: sowing
                crop_end_date:
                crop_end_type: maturity
                max_duration: 300
            TimedEvents:
            -   event_signal: irrigate
                name:  Timed irrigation events
                comment: All irrigation amounts in cm
                events_table:
                - 2000-05-25: {irrigation_amount: 3.0}
                - 2000-06-30: {irrigation_amount: 2.5}
            StateEvents:
            -   event_signal: apply_npk
                event_state: DVS
                zero_condition: rising
                name: DVS-based N/P/K application table
                comment: all fertilizer amounts in kg/ha
                events_table:
                - 0.3: {N_amount : 1, P_amount: 3, K_amount: 4}
                - 0.6: {N_amount: 11, P_amount: 13, K_amount: 14}
                - 1.12: {N_amount: 21, P_amount: 23, K_amount: 24}
        - 2000-09-01:
            CropCalendar:
            TimedEvents:
            StateEvents
        - 2001-03-01:
            CropCalendar:
                crop_name: maize
                variety_name: fodder-maize
                crop_start_date: 2001-04-15
                crop_start_type: sowing
                crop_end_date:
                crop_end_type: maturity
                max_duration: 200
            TimedEvents:
            -   event_signal: irrigate
                name:  Timed irrigation events
                comment: All irrigation amounts in cm
                events_table:
                - 2001-06-01: {irrigation_amount: 2.0}
                - 2001-07-21: {irrigation_amount: 5.0}
                - 2001-08-18: {irrigation_amount: 3.0}
                - 2001-09-19: {irrigation_amount: 2.5}
            -   event_signal: apply_npk
                name:  Timed N/P/K application table
                comment: All fertilizer amounts in kg/ha
                events_table:
                - 2001-05-25: {N_amount : 50, P_amount: 25, K_amount: 22}
                - 2001-07-05: {N_amount : 70, P_amount: 35, K_amount: 32}
            StateEvents:

    """

    # campaign start dates
    campaign_start_dates = List()

    # Overall engine start date and end date
    _start_date = Instance(date)
    _end_date = Instance(date)

    # campaign definitions
    crop_calendars = List()

    _tmp_date = None  # Helper variable
    _icampaign = 0  # count the campaigns

    def initialize(self, kiosk, agromanagement):
        """Initialize the AgroManager.

        :param kiosk: A PCSE variable Kiosk
        :param agromanagement: the agromanagement definition, see the example above in YAML.
        """


        self.kiosk = kiosk
        self.crop_calendars = []
        self.campaign_start_dates = []

        # Connect CROP_FINISH signal with handler
        self._connect_signal(self._on_CROP_FINISH, signals.crop_finish)

        # If there is an "AgroManagement" item defined then we first need to get
        # the contents defined within that item
        if "AgroManagement" in agromanagement:
            agromanagement = agromanagement["AgroManagement"]

        # First get and validate the dates of the different campaigns
        for campaign in agromanagement:
            # Check if campaign start dates is in chronological order
            campaign_start_date = take_first(campaign.keys())
            self._check_campaign_date(campaign_start_date)
            self.campaign_start_dates.append(campaign_start_date)

        # Add None to the list of campaign dates to signal the end of the
        # number of campaigns.
        self.campaign_start_dates.append(None)

        # Walk through the different campaigns and build crop calendars and
        # timed/state event dispatchers
        for campaign, campaign_start, next_campaign in \
                zip(agromanagement, self.campaign_start_dates[:-1], self.campaign_start_dates[1:]):

            # Get the campaign definition for the start date
            campaign_def = campaign[campaign_start]

            if self._is_empty_campaign(campaign_def):  # no campaign definition for this campaign, e.g. fallow
                self.crop_calendars.append(None)
                continue

            # get crop calendar definition for this campaign
            cc_def = campaign_def['CropCalendar']
            if cc_def is not None:
                cc = CropCalendar(kiosk, **cc_def)
                cc.validate(campaign_start, next_campaign)
                self.crop_calendars.append(cc)
            else:
                self.crop_calendars.append(None)


    def _is_empty_campaign(self, campaign_def):
        """"Check if the campaign definition is empty"""

        if campaign_def is None:
            return True

        attrs = ["CropCalendar", "TimedEvents", "StateEvents"]
        r = []
        for attr in attrs:
            if attr in campaign_def:
                if campaign_def[attr] is None:
                    r.append(True)
                else:
                    r.append(False)
        if r == [True]*3:
            return True

        return False

    @property
    def start_date(self):
        """Retrieves the start date of the agromanagement sequence, e.g. the first simulation date

        :return: a date object
        """
        if self._start_date is None:
            self._start_date = take_first(self.campaign_start_dates)

        return self._start_date

    @property
    def end_date(self):
        """Retrieves the end date of the agromanagement sequence, e.g. the last simulation date.

        :return: a date object

        Getting the last simulation date is more complicated because there are two options.

        **1. Adding an explicit trailing empty campaign**

        The first option is to explicitly define the end date of the simulation by adding a
        'trailing empty campaign' to the agromanagement definition.
        An example of an agromanagement definition with a 'trailing empty campaigns' (YAML format) is
        given below. This example will run the simulation until 2001-01-01::

            Version: 1.0
            AgroManagement:
            - 1999-08-01:
                CropCalendar:
                    crop_name: winter-wheat
                    variety_name: winter-wheat
                    crop_start_date: 1999-09-15
                    crop_start_type: sowing
                    crop_end_date:
                    crop_end_type: maturity
                    max_duration: 300
                TimedEvents:
                StateEvents:
            - 2001-01-01:

        Note that in configurations where the last campaign contains a definition for state events, a trailing
        empty campaign *must* be provided because the end date cannot be determined. The following campaign
        definition will therefore lead to an error::

            Version: 1.0
            AgroManagement:
            - 2001-01-01:
                CropCalendar:
                    crop_name: maize
                    variety_name: fodder-maize
                    crop_start_date: 2001-04-15
                    crop_start_type: sowing
                    crop_end_date:
                    crop_end_type: maturity
                    max_duration: 200
                TimedEvents:
                StateEvents:
                -   event_signal: apply_npk
                    event_state: DVS
                    zero_condition: rising
                    name: DVS-based N/P/K application table
                    comment: all fertilizer amounts in kg/ha
                    events_table:
                    - 0.3: {N_amount : 1, P_amount: 3, K_amount: 4}
                    - 0.6: {N_amount: 11, P_amount: 13, K_amount: 14}
                    - 1.12: {N_amount: 21, P_amount: 23, K_amount: 24}


        **2. Without an explicit trailing campaign**

        The second option is that there is no trailing empty campaign and in that case the end date of the simulation
        is retrieved from the crop calendar and/or the timed events that are scheduled. In the example below, the
        end date will be 2000-08-05 as this is the harvest date and there are no timed events scheduled after this
        date::

            Version: 1.0
            AgroManagement:
            - 1999-09-01:
                CropCalendar:
                    crop_name: wheat
                    variety_name: winter-wheat
                    crop_start_date: 1999-10-01
                    crop_start_type: sowing
                    crop_end_date: 2000-08-05
                    crop_end_type: harvest
                    max_duration: 330
                TimedEvents:
                -   event_signal: irrigate
                    name:  Timed irrigation events
                    comment: All irrigation amounts in cm
                    events_table:
                    - 2000-05-01: {irrigation_amount: 2, efficiency: 0.7}
                    - 2000-06-21: {irrigation_amount: 5, efficiency: 0.7}
                    - 2000-07-18: {irrigation_amount: 3, efficiency: 0.7}
                StateEvents:

        In the case that there is no harvest date provided and the crop runs till maturity, the end date from
        the crop calendar will be estimated as the crop_start_date plus the max_duration.

        """
        if self._end_date is None:

            # First check if the last campaign definition is an empty trailing campaign and use that date.
            if self.crop_calendars[-1] is None:
                self._end_date = self.campaign_start_dates[-2]  # use -2 here because None is
                                                                # appended to campaign_start_dates
                return self._end_date

            # Walk over the crop calendars and timed events to get the last date.
            cc_dates = []
            for cc in self.crop_calendars:
                if cc is not None:
                    cc_dates.append(cc.get_end_date())

            # If no end dates can be found raise an error because the agromanagement sequence
            # consists only of empty campaigns
            if not cc_dates:
                msg = "Empty agromanagement definition: no campaigns with crop calendars"
                raise exc.PCSEError(msg)

            end_date = date(1, 1, 1)
            if cc_dates:
                end_date = max(max(cc_dates), end_date)

            self._end_date = end_date

        return self._end_date

    def _check_campaign_date(self, campaign_start_date):
        """
        :param campaign_start_date: Start date of the agricultural campaign
        :return: None
        """
        if not isinstance(campaign_start_date, date):
            msg = "Campaign start must be given as a date."
            raise exc.PCSEError(msg)

        if self._tmp_date is None:
            self._tmp_date = campaign_start_date
        else:
            if campaign_start_date <= self._tmp_date:
                msg = "The agricultural campaigns are not sequential " \
                      "in the agromanagement definition."
                raise exc.PCSEError(msg)


    def __call__(self, day, drv):
        """Calls the AgroManager to execute and crop calendar actions, timed or state events.

        :param day: The current simulation date
        :param drv: The driving variables for the current day
        :return: None
        """

        # Check if the agromanager should switch to a new campaign
        if day == self.campaign_start_dates[self._icampaign+1]:
            self._icampaign += 1
            # if new campaign, throw out the previous campaign definition
            self.crop_calendars.pop(0)

        # call handlers for the crop calendar, timed and state events
        if self.crop_calendars[0] is not None:
            self.crop_calendars[0](day)


    def _on_CROP_FINISH(self, day):
        """Send signal to terminate after the crop cycle finishes.

        The simulation will be terminated when the following conditions are met:
        1. There are no campaigns defined after the current campaign
        2. There are no StateEvents active
        3. There are no TimedEvents scheduled after the current date.
        """


        if self.campaign_start_dates[self._icampaign+1] is not None:
            return  #  e.g. There is a next campaign defined

        self._send_signal(signal=signals.terminate)


    @property
    def ndays_in_crop_cycle(self):
        """Returns the number of days of the current cropping cycle.

        Returns zero if no crop cycle is active.
        """

        if self.crop_calendars[0] is None:
            return 0
        else:
            return self.crop_calendars[0].duration
