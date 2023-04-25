import streamlit as st
import PIL
import requests
import io

image_url = 'https://nrs.objectstore.gov.bc.ca/qamxjr/snowpack_archive/plot/modis/basins/2023.03.20/ADAMS_RIVER_NEAR_SQUILAX.png'

resp = requests.get(image_url)
image = PIL.Image.open(io.BytesIO(resp.content))

st.title('Snowpack analysis')

st.image(image, caption='a picture!')
