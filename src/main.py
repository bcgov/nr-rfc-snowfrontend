import streamlit as st
import logging.config
import os.path
import logging
import data_interface
import constants


if 'logger' not in st.session_state:

    log_config_path = os.path.realpath(os.path.join(os.path.dirname(__file__), 'logging.config'))
    logging.config.fileConfig(log_config_path)
    LOGGER = logging.getLogger(__name__)
    st.session_state.logger = LOGGER
    LOGGER.debug(f"name: {__name__}")
else:
    LOGGER = st.session_state.logger

# store this in the state so it gets retained, reducing round trips
# to object storage
SPD = data_interface.SnowPackData()

st.set_page_config(
    page_title="Historical Snowpack Analysis",
    page_icon="❄"
)

DISPLAY = st.container()

# session state variables
if 'wat_or_basin' not in st.session_state:
    st.session_state['wat_or_basin'] = constants.WAT_BASIN_OPTIONS[0]
    LOGGER.debug(f"setting wat_or_basin for first time: {st.session_state.wat_or_basin}")

if 'area_name' not in st.session_state:
    st.session_state['area_name'] = "Boundary"
    LOGGER.debug(f"area name: {st.session_state.area_name}")
    #show_images(area_type=data_interface.AreaType['watersheds'], area_name='Boundary')


def wat_basin_changed(*args, **kwargs):
    LOGGER.debug(f"watbas - area type is: {st.session_state['wat_or_basin']}")
    LOGGER.debug(f"watbas - satellites are {st.session_state['sat']}")
    LOGGER.debug(f"watbas - area name: {st.session_state.area_name}")
    # if the are type: (watershed/basin) changes then we need to
    # 1) reload the basin / watershed names
    # 2) choose default basin / watershed
    # 3) reload the images
    post_area_name_sidebar(st.session_state['wat_or_basin'])

    #cur_sat = data_interface.Satellite[st.session_state['sat']]
    area_type = data_interface.AreaType[st.session_state['wat_or_basin']]
    name_url_dict = SPD.get_names(sat=cur_sat, area_type=area_type)


    wat_basin = data_interface.AreaType[st.session_state.wat_or_basin.lower()]
    show_images(area_type=wat_basin,
                area_name=st.session_state.area_name,
                sat_list=st.session_state.sat)


def breakdown_type(*args, **kwargs):
    LOGGER.debug(f"area type is: {st.session_state['wat_or_basin']}")
    LOGGER.debug(f"satellites are {st.session_state['sat']}")
    LOGGER.debug(f"area name: {st.session_state.area_name}")

    # convert the strings for satellite(sat) and area_type to enumerations
    wat_basin = data_interface.AreaType[st.session_state.wat_or_basin.lower()]

    #sat = data_interface.Satellite[st.session_state['sat'][0].lower()]

    # get the dates that are available for the modis sat.. modis data is usually
    # more quickly processed than the viirs, and therefor the viirs is usually
    # a subset of modis... so just getting dates for modis then iterate
    # over those dates making the viirs data visiible if it can be found
    show_images(area_type=wat_basin,
                area_name=st.session_state.area_name,
                sat_list=st.session_state.sat)

def sat_changed(*args, **kwargs):
    LOGGER.debug(f"sat - area type is: {st.session_state['wat_or_basin']}")
    LOGGER.debug(f"sat - satellites are {st.session_state['sat']}")
    if ('area_name' in st.session_state) and st.session_state.area_name:
        # only update the images if the area type, and an actual area
        # have been selected.
        LOGGER.debug(f"sat - area name: {st.session_state.area_name}")

        #names = list(sat_name_url_dict['modis'].keys())
        name_url_dict = SPD.get_names(
            sat=data_interface.Satellite['modis'], # area names are independent of satellite so just using modis here
            area_type=data_interface.AreaType[st.session_state.wat_or_basin.lower()])
        names = list(name_url_dict.keys())

        wat_basin = data_interface.AreaType[st.session_state.wat_or_basin.lower()]

        show_images(area_type=wat_basin,
                    area_name=st.session_state.area_name,
                    sat_list=st.session_state.sat)

def show_images(area_type, area_name, sat_list):
    # sat_list - list of sattellite data to display
    # determine what satellites are selected, use modis if its in the list

    LOGGER.debug(f"satlist: {sat_list}")
    if not sat_list:
        with DISPLAY.empty():
            DISPLAY.write(f'## No Satellites are currently selected for viewing')
    else:
        if 'modis' in st.session_state.sat:
            cur_sat_str = 'modis'
        else:
            cur_sat_str = sat_list[0]
        cur_sat = data_interface.Satellite[cur_sat_str]

        cur_sat_date_list = SPD.get_dates(
            sat=cur_sat,
            area_type=area_type,
            number_of_dates=constants.DAYS_BACK
            )
        cur_sat_date_list.sort(reverse=True)
        with DISPLAY.empty():
            # Want to display the data for the given satellite / area type
            # combination
            # sooo
            # ----
            # Title: Area_name
            # Date: date
            # ----------------
            # satellite: sat_name
            # <image>
            # satellite: sat_name
            # <image>
            #
            # Date: date
            # --------------
            # satellite: sat_name
            # <image>
            # satellite: sat_name
            # <image>
            #
            # ...blah blah blah
            DISPLAY.write(f'# {area_type.name[0:-1].capitalize()}: *{area_name}* ')
            for date in cur_sat_date_list:
                first_sat = True
                LOGGER.debug(f"satellites: {sat_list} {type(sat_list)}")
                for sat_str in sat_list:
                    LOGGER.debug(f"sat_str: {sat_str}")
                    if first_sat:
                        first_sat = False
                        DISPLAY.write(f'### Date: *{date}* ')

                    sat_url = SPD.get_url_by_date(
                                date_str=date,
                                sat=data_interface.Satellite[sat_str],
                                area_type=area_type,
                                area_name=area_name)
                    LOGGER.debug(f"{sat_str} url: - {sat_url}- {type(sat_url)}")
                    DISPLAY.write(f'#### Satellite: *{sat_str}*')
                    if sat_url:
                        DISPLAY.image(
                            str(sat_url),
                            width=600, # Manually Adjust the width of the image as per requirement
                        )
                DISPLAY.write('---------')


st.sidebar.success("Configure what you want to view.")

# -- Satellite product to view
# Add callbacks to change display when this is changed
sat = st.sidebar.multiselect(
    label="Which Satelite based Snowpack Product",
    options=constants.SAT_OPTIONS,
    default=constants.SAT_OPTIONS,
    on_change=sat_changed,
    key='sat'
)
LOGGER.debug(f"sat from multiselect: {sat}")

# -- Watershed or Basin radio button
wat_or_basin = st.sidebar.radio(
    "View data by Watershed or Basin",
    on_change=wat_basin_changed,
    key='wat_or_basin',
    index=0,
    options=constants.WAT_BASIN_OPTIONS
    )

DISPLAY.write("# Historical Snowpack Analysis ❄")

# get the possible options for watershed / Basin
# and populate into a select list
LOGGER.debug(f"watershed or basin: {wat_or_basin}")
LOGGER.debug(f"satellites: {sat} {st.session_state.sat}")

def post_area_name_sidebar(area_type_str):
    global names
    global sidebar_area_selector
    LOGGER.debug(f"area type string: {area_type_str}")
    area_type = data_interface.AreaType[area_type_str]
    cur_sat = data_interface.Satellite['modis'] # always default

    name_url_dict = SPD.get_names(
        sat=cur_sat,
        area_type=area_type)
    names = list(name_url_dict.keys())

    LOGGER.debug(f"watershed or basin: {wat_or_basin}")
    LOGGER.debug(f"names: {names[0:4]}...")
    LOGGER.debug(f"sidebar_area_selector: {sidebar_area_selector}")
    with sidebar_area_selector.empty():
        option = sidebar_area_selector.selectbox(
            label=f'Which {wat_or_basin}',
            options=names,
            key='area_name',
            on_change=breakdown_type,
            index=0)

# get the data
sat_name_url_dict = {}
for sat_str in sat:
    LOGGER.debug(f"sat_str: {sat_str}")
    cur_sat = data_interface.Satellite[sat_str]
    area_type = data_interface.AreaType[wat_or_basin]
    name_url_dict = SPD.get_names(sat=cur_sat, area_type=area_type)
    sat_name_url_dict[sat_str] = name_url_dict


sidebar_area_selector = st.sidebar.container()

LOGGER.debug(f"session state sat: {st.session_state.sat}")
if st.session_state.sat:
    # this is the default satellite - modis
    # names = list(sat_name_url_dict['modis'].keys())
    # LOGGER.debug(f"names: {type(names)} {names}")

    # # populate the area pulldown
    # option = st.sidebar.selectbox(
    #     label=f'Which {wat_or_basin}',
    #     options=names,
    #     key='area_name',
    #     on_change=breakdown_type,
    #     index=0)
    post_area_name_sidebar(wat_or_basin)

# show_images(area_type=data_interface.AreaType['watersheds'], area_name='Boundary')

# # # load initial view
if 'firstload' not in st.session_state:
    LOGGER.debug("loading first view")
    show_images(area_type=data_interface.AreaType['watersheds'],
                area_name='Boundary',
                sat_list=st.session_state.sat)
    st.session_state.firstload = True
