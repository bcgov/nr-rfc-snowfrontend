import NRUtil.NRObjStoreUtil
import NRUtil.constants
import os.path
import logging
import enum
import constants
from typing_extensions import TypedDict
import datetime

LOGGER = logging.getLogger(__name__)


# class Satellite(enum.Enum):
#     modis = 1
#     viirs = 2
Satellite = enum.Enum('Satellite', constants.SAT_OPTIONS)
AreaType = enum.Enum('AreaType', constants.WAT_BASIN_OPTIONS)


class CacheData():
    """interface to cache data retrieved from object store to reduce the number
    of times the object store api needs to be called
    """
    def __init__(self):
        self.CACHE_DATA = {}
        self.CACHE_DATES = {}

    def get_cache(self,
                  sat: Satellite,
                  area_type:AreaType,
                  date_str: str) -> dict:
        """returns cached data for a satellite/area_type/date combination.
        if the data hasn't been cached for that combo retuns None

        :param sat: the satellite type
        :type sat: Satellite
        :param area_type: area type, at time of writing Basins/Watersheds
        :type area_type: AreaType
        :param date_str: the date string for the data to be retrieved, format
            should be 'YYYY.MM.DD'
        :type date_str: str
        :return: dictionary with the name of the area / url to image of the
            snowpack comparison
        :rtype: dict
        """
        cache_data = self._get_cache(sat, area_type, date_str, self.CACHE_DATA)
        return cache_data

    # TODO: define mypy type for data
    def set_cache(self,
                  sat: Satellite,
                  area_type:AreaType,
                  date_str:str,
                  data):
         self._set_cache(sat, area_type, date_str, data, self.CACHE_DATA)

    def _get_cache(self, sat: Satellite,
                  area_type:AreaType, date_str, cache):
        cache_data = None
        if (( sat in cache ) and \
                area_type in cache[sat]) and \
                date_str in cache[sat][area_type] and \
                cache[sat][area_type][date_str]:
            cache_data = cache[sat][area_type][date_str]

    def _set_cache(self,
                  sat: Satellite,
                  area_type:AreaType,
                  date_str:str,
                  data,
                  cache):
        if sat not in cache:
            cache[sat] = {}
        if area_type not in cache[sat]:
            cache[sat][area_type] = {}
        LOGGER.debug(f"date added for: {date_str}")
        cache[sat][area_type][date_str] = data

    def get_cache_dates(self,
                        sat: Satellite,
                        area_type:AreaType) -> dict:
        dates = []
        if (    (sat in self.CACHE_DATES) and \
                area_type in self.CACHE_DATES[sat] ) and \
                self.CACHE_DATES[sat][area_type]:
           dates = self.CACHE_DATES[sat][area_type]
           dates.sort()
        LOGGER.debug(f"dates from cache: {dates}")
        return dates

    def set_cache_dates(self,
                        sat: Satellite,
                        area_type:AreaType,
                        dates) -> dict:
        if not sat in self.CACHE_DATES:
            self.CACHE_DATES[sat] = {}
        if not area_type in self.CACHE_DATES[sat]:
            self.CACHE_DATES[sat][area_type] = []
        self.CACHE_DATES[sat][area_type].extend(dates)

class SnowPackData():
    def __init__(self):
        self.objstor = NRUtil.NRObjStoreUtil.ObjectStoreUtil()
        self.plotdir = 'plot'
        self.archive_dir = 'snowpack_archive'
        self.cache = CacheData()
        self.data_retrieved = False # marker to know if the data retrieval and
                                    # caching has been called

    def get_all_data(self):
        """loads and caches all the data from object store that will be required
        to display to various images.
        """
        if not self.data_retrieved:
            date_strings = self.get_date_strings()

            for date_string in date_strings:
                for sat_str in constants.SAT_OPTIONS:
                    for area_type_str in constants.WAT_BASIN_OPTIONS:
                        sat = Satellite[sat_str]
                        area_type = AreaType[area_type_str]
                        dates_exist = self.get_dates(sat=sat, area_type=area_type)
                        if date_string in dates_exist:
                            LOGGER.info(f'getting data for sat={sat_str}, area_type={area_type_str}, {date_string}')
                            self.get_names(sat=sat,
                                        area_type=area_type,
                                        date_str=date_string)
        self.data_retrieved = True

    def get_date_strings(self, days_back=10) -> list[str]:
        """creates a list of date strings in the form 'YYYY.MM.DD'.  By
        default generates 10, but that is a configurable option.

        :return: a list of strings containing date strings from yesterday back
            'days_back' number of days
        :rtype: list(str)
        """
        # gets date strings for now back to the number of days calculated
        date_str_list = []
        now = datetime.datetime.now()
        for days_back in range(1, days_back + 1):
            tmp_date = now - datetime.timedelta(days=days_back)
            date_str = tmp_date.strftime('%Y.%m.%d')
            date_str_list.append(date_str)
        return date_str_list

    def get_names(self,
                  sat: Satellite=Satellite.modis,
                  area_type:AreaType=AreaType.watersheds,
                  date_str=None,
                  publish=False
    ):
        """For a given satellite / area_type / date_str, will return a
        dictionary, where the keys are the area_type names, and the values
        are the url's to the images that describe the historical snowpack
        comparisons.

        first checks the cache, if the cache doesn't have the data then makes
        a call to object storage, and then writes to the cache.

        Needs the following env vars to be populated to function correctly:
            * OBJ_STORE_BUCKET
            * OBJ_STORE_SECRET
            * OBJ_STORE_USER
            * OBJ_STORE_HOST

        :param sat: _description_, defaults to Satellite.modis
        :type sat: Satellite, optional
        :param area_type: _description_, defaults to AreaType.watersheds
        :type area_type: AreaType, optional
        :param date_str: _description_, defaults to None
        :type date_str: _type_, optional
        :return: _description_
        :rtype: _type_
        """
        if date_str is None:
            dates = self.get_dates(sat=sat, area_type=area_type)
            date_str = dates[0]

        cache_data = self.cache.get_cache(sat=sat, area_type=area_type, date_str=date_str)

        if not cache_data:

            plot_dir = self.get_plot_dir(sat=sat, area_type=area_type, date_str=date_str)
            obj_list = self.objstor.list_objects(objstore_dir=plot_dir, recursive=False, return_file_names_only=True)

            # https://nrs.objectstore.gov.bc.ca/qamxjr/snowpack_archive/plot/modis/basins/2023.03.20/ASHNOLA_RIVER_NEAR_KEREMEOS.png
            #
            # ostore_env_vars_names = ['OBJ_STORE_BUCKET', 'OBJ_STORE_SECRET',
            #                          'OBJ_STORE_USER', 'OBJ_STORE_HOST']


            # finally pull just the file name out of the obj_list and remove
            # any suffix, finally replace any _ with spaces
            names_list = {}
            for cur_obj in obj_list:
                file_name = os.path.basename(cur_obj)
                file_name_no_suffix = os.path.splitext(file_name)[0]
                file_name_spaces = file_name_no_suffix.replace("_", " ")
                obj_store_url = f'https://{NRUtil.constants.OBJ_STORE_HOST}/{NRUtil.constants.OBJ_STORE_BUCKET}/{cur_obj}'
                names_list[file_name_spaces] = obj_store_url

                # todo: this should later get removed and be part of the upload
                #       scripts
                if publish:
                    self.objstor.set_public_permissions(object_name=cur_obj)
            self.cache.set_cache(sat=sat, area_type=area_type, date_str=date_str,
                                 data=names_list)
            cache_data = names_list
        return cache_data

    def get_dates(self,
                  sat: Satellite=Satellite.modis,
                  area_type:AreaType=AreaType.watersheds,
                  number_of_dates: int=constants.DAYS_BACK
                ):
        cached_dates = self.cache.get_cache_dates(sat=sat, area_type=area_type)

        LOGGER.debug(f"cached dates: {cached_dates}")
        if not cached_dates:
            plot_dir = self.get_plot_dir(sat=sat)
            #  objstore_dir=None, recursive=True, return_file_names_only=False

            obj_list = self.objstor.list_objects(objstore_dir=plot_dir, recursive=False, return_file_names_only=True)
            LOGGER.debug(f"obj_list: {obj_list}")

            # strip off the trailing '/' character and create a list of only
            # dates
            dates = []
            for cur_date in obj_list:
                if cur_date[-1] == '/':
                    cur_date = cur_date[:-1]
                dates.append(os.path.basename(cur_date))

            cached_dates = dates
            self.cache.set_cache_dates(sat=sat, area_type=area_type, dates=cached_dates)

            LOGGER.debug(f"dates: {dates}")
        if cached_dates:
            cached_dates.sort(reverse=True)
            # trim to latest 5 then revert to ascending sort
            cached_dates = cached_dates[0:number_of_dates]
            cached_dates.sort()
        return cached_dates

    def get_plot_dir(self,
                     sat: Satellite=Satellite.modis,
                     area_type:AreaType=AreaType.watersheds,
                     date_str=None) -> str:
        """_summary_

        :param sat: _description_, defaults to Satellite.modis
        :type sat: Satellite, optional
        :param area_type: _description_, defaults to AreaType.watersheds
        :type area_type: AreaType, optional
        :param date_str: _description_, defaults to None
        :type date_str: _type_, optional
        :return: _description_
        :rtype: str
        """
        LOGGER.debug(f"sat: {sat.name}")
        #sat_str = sat

        plot_dir = os.path.join(self.archive_dir, self.plotdir, sat.name, area_type.name)
        if date_str:
            plot_dir = os.path.join(plot_dir, date_str)
        if plot_dir[0] == '/':
            plot_dir = plot_dir[1:]
        if plot_dir[-1] != '/':
            plot_dir = plot_dir + '/'
        LOGGER.debug(f"plot_dir: {plot_dir}")
        return plot_dir

    def get_url_by_date(self,
                         date_str:str,
                         area_name:str,
                         sat: Satellite=Satellite.modis,
                         area_type:AreaType=AreaType.watersheds
                         ):
        """for a given satellite / area type / date string, returns the url
        for that image if it exists.

        :param date_str: _description_
        :type date_str: _type_
        :param sat: _description_, defaults to Satellite.modis
        :type sat: Satellite, optional
        :param area_type: _description_, defaults to AreaType.watersheds
        :type area_type: AreaType, optional
        :return: the url for the specific satellite/area_type/area_name combo
        :rtype: str
        """
        url = None
        # makes sure that the cache has been loaded
        dates_exist = self.get_dates(sat=sat, area_type=area_type)
        LOGGER.debug(f"dates for sat: {sat.name} area type: {area_type.name} date: {dates_exist}")
        if date_str in dates_exist:
            names = self.get_names(sat=sat, area_type=area_type, date_str=date_str)
            if area_name in names:
                url = names[area_name]
        return url


if __name__ == '__main__':

    LOGGER = logging.getLogger()
    LOGGER.setLevel(logging.DEBUG)
    hndlr = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(lineno)d - %(message)s')
    hndlr.setFormatter(formatter)
    LOGGER.addHandler(hndlr)
    LOGGER.debug("test")

    info_loggers = ['botocore.auth', 'botocore.hooks', 'botocore.endpoint',
                    'botocore.regions', 'botocore.retryhandler',
                    'botocore.parsers', 'urllib3.connectionpool',
                    'botocore.httpsession', 'NRUtil.NRObjStoreUtil']
    for log_name in info_loggers:
        tmp_log = logging.getLogger(log_name)
        tmp_log.setLevel(logging.INFO)



    spd = SnowPackData()

    # hacking - publish of data
    sat = Satellite['viirs']
    area_type = AreaType['watersheds']
    names_dict = spd.get_names(sat=sat,
                               area_type=area_type,
                               date_str='2023.03.23',
                               publish=True)
    import sys
    sys.exit()

    spd.get_all_data()

    dates = spd.get_dates()
    LOGGER.debug(f"dates returned: {dates}")

    # area_type = AreaType['basins']
    # LOGGER.debug(f"area type: {area_type.name}")

    names_dict = spd.get_names()
    LOGGER.debug(f"names dictionary: {names_dict}")

    area_name = 'West Kootenay'
    url = spd.get_url_by_date(
                date_str='2023.03.22',
                sat=Satellite['modis'],
                area_type=AreaType['watersheds'],
                area_name=area_name)
    LOGGER.debug(f"url for {area_name} is {url}")
