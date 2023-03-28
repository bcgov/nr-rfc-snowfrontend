import streamlit as st
import logging.config
import os.path
import logging
import data_interface
import constants


if 'logger' not in st.session_state:

    log_config_path = os.path.realpath(os.path.join(os.path.dirname(__file__), '..', 'config', 'logging.config'))
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

# TODO: change to select both by default
if 'sat' not in st.session_state:
    st.session_state['sat'] = constants.SAT_OPTIONS[0]
    LOGGER.debug(f"setting the satellite type: {st.session_state.sat}")

if 'area_name' not in st.session_state:
    st.session_state['area_name'] = "Boundary"
    LOGGER.debug(f"area name: {st.session_state.area_name}")
    #show_images(area_type=data_interface.AreaType['watersheds'], area_name='Boundary')


def swap_area_type(*args, **kwargs):
    pass

def breakdown_type(*args, **kwargs):
    LOGGER.debug(f"area type is: {st.session_state['wat_or_basin']}")
    LOGGER.debug(f"satellites are {st.session_state['sat']}")
    LOGGER.debug(f"area name: {st.session_state.area_name}")

    # convert the strings for satellite(sat) and area_type to enumerations
    wat_basin = data_interface.AreaType[st.session_state.wat_or_basin.lower()]
    sat = data_interface.Satellite[st.session_state['sat'].lower()]

    # get the dates that are available for the modis sat.. modis data is usually
    # more quickly processed than the viirs, and therefor the viirs is usually
    # a subset of modis... so just getting dates for modis then iterate
    # over those dates making the viirs data visiible if it can be found
    show_images(area_type=wat_basin, area_name=st.session_state.area_name)

def show_images(area_type, area_name):
    # determine what satellites are selected, use modis if its in the list
    if 'modis' in st.session_state.sat:
        cur_sat_str = 'modis'
    else:
        cur_sat_str = st.session_state.sat[0]
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
            #for sat_str in st.session_state.sat:
            url_modis = SPD.get_url_by_date(
                date_str=date,
                sat=data_interface.Satellite['modis'],
                area_type=area_type,
                area_name=area_name)
            url_viirs = SPD.get_url_by_date(
                date_str=date,
                sat=data_interface.Satellite['viirs'],
                area_type=area_type,
                area_name=area_name)
            LOGGER.debug(f"modis url: - {url_modis}- {type(url_modis)}")
            LOGGER.debug(f"viirs url: {url_viirs} {type(url_viirs)}")

            DISPLAY.write(f'### Date: *{date}* ')
            DISPLAY.write(f'#### Satellite: *MODIS*')
            DISPLAY.image(
                    str(url_modis),
                    width=600, # Manually Adjust the width of the image as per requirement
                )
            if url_viirs:
                DISPLAY.write(f'#### Satellite: *VIIRS*')
                DISPLAY.image(
                        url_viirs,
                        width=600, # Manually Adjust the width of the image as per requirement
                    )
            DISPLAY.write('---------')


st.sidebar.success("Configure what you want to view.")

# -- Satellite product to view
# Add callbacks to change display when this is changed
satellite = st.sidebar.multiselect(
    label="Which Satelite based Snowpack Product",
    options=constants.SAT_OPTIONS,
    default=constants.SAT_OPTIONS
)

# -- Watershed or Basin radio button
wat_or_basin = st.sidebar.radio(
    "View data by Watershed or Basin",
    on_change=breakdown_type,
    #args=[st.session_state['wat_or_basin']],
    key='wat_or_basin',
    index=0,
    options=constants.WAT_BASIN_OPTIONS
    )

DISPLAY.write("# Historical Snowpack Analysis ❄")

# get the possible options for watershed / Basin
# and populate into a select list
LOGGER.debug(f"watershed or basin: {wat_or_basin}")
LOGGER.debug(f"satellites: {satellite}")

# get the data
sat_name_url_dict = {}
for sat_str in satellite:
    sat = data_interface.Satellite[sat_str]
    area_type = data_interface.AreaType[wat_or_basin]
    name_url_dict = SPD.get_names(sat=sat, area_type=area_type)
    sat_name_url_dict[sat_str] = name_url_dict

# TODO: come back and deal with multi sat
names = list(sat_name_url_dict['modis'].keys())

LOGGER.debug(f"names: {type(names)} {names}")

#st.spinner(text=f"loading {wat_or_basin} list...")

# populate the area pulldown
option = st.sidebar.selectbox(
    label=f'Which {wat_or_basin}',
    options=names,
    key='area_name',
    on_change=breakdown_type,
    index=0)

# show_images(area_type=data_interface.AreaType['watersheds'], area_name='Boundary')

# # # load initial view
if 'firstload' not in st.session_state:
    LOGGER.debug("loading first view")
    show_images(area_type=data_interface.AreaType['watersheds'], area_name='Boundary')
    st.session_state.firstload = True
