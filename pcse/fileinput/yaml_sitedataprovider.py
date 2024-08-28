# -*- coding: utf-8 -*-
# Copyright (c) 2004-2022 Wageningen Environmental Research, Wageningen-UR
# Allard de Wit (allard.dewit@wur.nl), August 2022
# Modified by Will Solow, Oregon State University August 2024
import logging
import os, sys

v = sys.version_info
if v.major == 3:
    # For Python 3.0 and later
    from urllib.request import urlopen
    from urllib.error import URLError
    import pickle
else:
    # Fall back to Python 2's urllib2
    from urllib2 import urlopen, URLError
    import cPickle as pickle

import yaml

from ..base import MultiCropDataProvider
from .. import exceptions as exc
from .. import settings
from ..util import version_tuple


class YAMLSiteDataProvider(MultiCropDataProvider):
    """A site data provider for reading site and soil parameter sets stored in the YAML format.
       This directly extends the crop format by allowing multiple sites to be created
       with different parameters

        :param fpath: full path to directory containing YAML files
        :param repository: URL to repository containg YAML files. This url should be
         the *raw* content (e.g. starting with 'https://raw.githubusercontent.com')
        :param force_reload: If set to True, the cache file is ignored and al
         parameters are reloaded (default False).

    This site data provider can read and store the parameter sets for multiple
    sites which is different from most other site data providers that only can
    hold data for a single site/soil type.
    """
    default_repository = "https://raw.githubusercontent.com/ajwdewit/WOFOST_crop_parameters/master/"

    HTTP_OK = 200
    current_site_name = None
    current_variation_name = None

    # Compatibility of data provider with YAML parameter file version
    compatible_version = "1.0.0"

    def __init__(self, fpath=None, repository=None, force_reload=False):
        MultiCropDataProvider.__init__(self)

        if force_reload is True or self._load_cache(fpath) is False:  # either force a reload or load cache fails
            # enforce a clear state
            self.clear()
            self._store.clear()

            if fpath is not None:
                self.read_local_repository(fpath)

            elif repository is not None:
                self.read_remote_repository(repository)

            else:
                msg = f"No path or URL specified where to find YAML site parameter files, " \
                      f"using default at {self.default_repository}"
                self.logger.info(msg)
                self.read_remote_repository(self.default_repository)

            with open(self._get_cache_fname(fpath), "wb") as fp:
                pickle.dump((self.compatible_version, self._store), fp, pickle.HIGHEST_PROTOCOL)

    def read_local_repository(self, fpath):
        """Reads the site YAML files on the local file system

        :param fpath: the location of the YAML files on the filesystem
        """
        yaml_file_names = self._get_yaml_files(fpath)
        for site_name, yaml_fname in yaml_file_names.items():
            with open(yaml_fname) as fp:
                parameters = yaml.safe_load(fp)
            self._check_version(parameters, site_fname=yaml_fname)
            self._add_site(site_name, parameters)

    def read_remote_repository(self, repository):
        """Reads the site files from a remote git repository

        :param repository: The url of the repository pointing to the URL where the raw inputs can be obtained.
            E.g. for github this is https://raw.githubusercontent.com/ajwdewit/WOFOST_crop_parameters/master
        :return:
        """

        if not repository.endswith("/"):
            repository += "/"
        self.repository = repository
        try:
            url = self.repository + "sites.yaml"
            response = urlopen(url)
            self.site_types = yaml.safe_load(response)["available_sites"]
        except URLError as e:
            msg = "Unable to find sites.yaml at '%s' due to: %s" % (url, e)
            raise exc.PCSEError(msg)

        for site_name in self.site_types:
            url = self.repository + site_name + ".yaml"
            try:
                response = urlopen(url)
            except URLError as e:
                msg = "Unable to open '%s' due to: %s" % (url, e)
                raise exc.PCSEError(msg)
            parameters = yaml.safe_load(response)
            self._check_version(parameters, site_fname=site_name)
            self._add_site(site_name, parameters)

    def _get_cache_fname(self, fpath):
        """Returns the name of the cache file for the CropDataProvider.
        """
        cache_fname = "%s.pkl" % self.__class__.__name__
        if fpath is None:
            cache_fname_fp = os.path.join(settings.METEO_CACHE_DIR, cache_fname)
        else:
            cache_fname_fp = os.path.join(fpath, cache_fname)
        return cache_fname_fp

    def _load_cache(self, fpath):
        """Loads the cache file if possible and returns True, else False.
        """
        try:
            cache_fname_fp = self._get_cache_fname(fpath)
            if os.path.exists(cache_fname_fp):

                # First we check that the cache file reflects the contents of the YAML files.
                # This only works for files not for github repos
                if fpath is not None:
                    yaml_file_names = self._get_yaml_files(fpath)
                    yaml_file_dates = [os.stat(fn).st_mtime for site,fn in yaml_file_names.items()]
                    # retrieve modification date of cache file
                    cache_date = os.stat(cache_fname_fp).st_mtime
                    # Ensure cache file is more recent then any of the YAML files
                    if any([d > cache_date for d in yaml_file_dates]):
                        return False

                # Now start loading the cache file
                with open(cache_fname_fp, "rb") as fp:
                    version, store = pickle.load(fp)
                if version_tuple(version) != version_tuple(self.compatible_version):
                    msg = "Cache file is from a different version of YAMLSiteDataProvider"
                    raise exc.PCSEError(msg)
                self._store = store
                return True

        except Exception as e:
            msg = "%s - Failed to load cache file: %s" % (self.__class__.__name__, e)
            print(msg)

        return False

    def _check_version(self, parameters, site_fname):
        """Checks the version of the parameter input with the version supported by this data provider.

        Raises an exception if the parameter set is incompatible.

        :param parameters: The parameter set loaded by YAML
        """
        try:
            v = parameters['Version']
            if version_tuple(v) != version_tuple(self.compatible_version):
                msg = "Version supported by %s is %s, while parameter set version is %s!"
                raise exc.PCSEError(msg % (self.__class__.__name__, xatible_version, parameters['Version']))
        except Exception as e:
            msg = f"Version check failed on site parameter file: {site_fname}"
            raise exc.PCSEError(msg)

    def _add_site(self, site_name, parameters):
        """Store the parameter sets for the different varieties for the given site.
        """
        variation_sets = parameters["SiteParameters"]["Variations"]
        self._store[site_name] = variation_sets

    def _get_yaml_files(self, fpath):
        """Returns all the files ending on *.yaml in the given path.
        """
        fname = os.path.join(fpath, "sites.yaml")
        if not os.path.exists(fname):
            msg = "Cannot find 'sites.yaml' at {f}".format(f=fname)
            raise exc.PCSEError(msg)
        site_names = yaml.safe_load(open(fname))["available_sites"]
        site_yaml_fnames = {site: os.path.join(fpath, site + ".yaml") for site in site_names}
        for site, fname in site_yaml_fnames.items():
            if not os.path.exists(fname):
                msg = f"Cannot find yaml file for site '{site}': {fname}"
                raise RuntimeError(msg)
        return site_yaml_fnames

    def set_active_site(self, site_name, variation_name):
        """Sets the parameters in the internal dict for given site_name and variation_name

        It first clears the active set of site/soil parameters in the internal dict.

        :param site_name: the name of the site
        :param variation_name: the variation for the given site
        """
        self.clear()
        if site_name not in self._store:
            msg = "Site name '%s' not available in %s " % (site_name, self.__class__.__name__)
            raise exc.PCSEError(msg)
        variation_sets = self._store[site_name]
        if variation_name not in variation_sets:
            msg = "Variation name '%s' not available for site '%s' in " \
                  "%s " % (variation_name, site_name, self.__class__.__name__)
            raise exc.PCSEError(msg)

        self.current_site_name = site_name
        self.current_variation_name = variation_name

        # Retrieve parameter name/values from input (ignore description and units)
        parameters = {k: v[0] for k, v in variation_sets[variation_name].items() if k != "Metadata"}
        # update internal dict with parameter values for this variety
        self.update(parameters)

    def get_site_variations(self):
        """Return the names of available sites and variations per site.

        :return: a dict of type {'site_name1': ['variation_name1', 'variation_name1', ...],
                                 'site_name2': [...]}
        """
        return {k: v.keys() for k, v in self._store.items()}

    def print_site_variations(self):
        """Gives a printed list of sites and variations on screen.
        """
        msg = ""
        for site, variation in self.get_site_variations().items():
            msg += "site '%s', available varieties:\n" % site
            for var in variation:
                msg += (" - '%s'\n" % var)
        print(msg)

    def __str__(self):
        if not self:
            msg = "%s - site and variation not set: no active site parameter set!\n" % self.__class__.__name__
            return msg
        else:
            msg = "%s - current active site '%s' with variation '%s'\n" % \
                  (self.__class__.__name__, self.current_site_name, self.current_variation_name)
            msg += "Available site parameters:\n %s" % str(dict.__str__(self))
            return msg

    @property
    def logger(self):
        loggername = "%s.%s" % (self.__class__.__module__,
                                self.__class__.__name__)
        return logging.getLogger(loggername)