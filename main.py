import streamlit as st

import utils
from pages.main_page import main_page
from pages.raw_data import raw_data_page
from pages.pump_curves import pump_curves_page
from pages.water_losses import water_losses_page
from pages.storage import storage_page
from pages.demand_analysis import demand_analysis_page

st.set_page_config(page_title="Alaska Dashboard", layout="wide")

pg_main = st.Page(main_page, title="Home")
pg_raw = st.Page(raw_data_page, title="Raw Data")
pg_dem_analysis = st.Page(demand_analysis_page, title="Demands Analysis")
pg_pumps = st.Page(pump_curves_page, title="Pump Curves")
pg_water_losses = st.Page(water_losses_page, title="Water Losses")
pg_storage = st.Page(storage_page, title="Storage")

nav = st.navigation([pg_main, pg_raw, pg_dem_analysis, pg_pumps, pg_water_losses, storage_page])

# Track current page in session_state
if "current_page" not in st.session_state:
    st.session_state.current_page = "Dashboard"

st.title("Alaska WDS Data Dashboard")
col1, col2, col3, col4, col5 = st.columns(5)
st.divider()

clicked = st.query_params.get("clicked")
with col1:
    utils.custom_button("resources/icon_raw_data.png", "Raw Data", button_id="raw")
    if clicked == "raw":
        st.switch_page(pg_raw)
with col2:
    utils.custom_button("resources/icon_demand.png", "Demands", button_id="demand")
    if clicked == "demand":
        st.switch_page(pg_dem_analysis)
with col3:
    utils.custom_button("resources/icon_pumps.png", "Pumps Curves", button_id="pumps")
    if clicked == "pumps":
        st.switch_page(pg_pumps)
with col4:
    utils.custom_button("resources/icon_backwash.png", "Backwash", button_id="backwash")
    if clicked == "backwash":
        st.switch_page(pg_water_losses)
with col5:
    utils.custom_button("resources/icon_tank.png", "Tank", button_id="tank")
    if clicked == "tank":
        st.switch_page(pg_storage)

nav.run()
