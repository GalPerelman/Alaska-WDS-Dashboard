import streamlit as st

from pages.main_page import main_page
from pages.raw_data import raw_data_page
from pages.pump_curves import pump_curves_page
from pages.demand_pattern import demands_page
from pages.water_losses import water_losses_page
from pages.storage import storage_page

st.set_page_config(page_title="Alaska Dashboard", layout="wide")

pg_main = st.Page(main_page, title="Home")
pg_raw = st.Page(raw_data_page, title="Raw Data")
pg_pumps = st.Page(pump_curves_page, title="Pump Curves")
pg_demand = st.Page(demands_page, title="Demand Patterns")
pg_water_losses = st.Page(water_losses_page, title="Water Losses")
pg_storage = st.Page(storage_page, title="Storage")

nav = st.navigation([pg_main, pg_raw, pg_pumps, pg_demand, pg_water_losses, storage_page])

# Track current page in session_state
if "current_page" not in st.session_state:
    st.session_state.current_page = "Dashboard"


st.title("Alaska WDS Data Dashboard")
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    if st.button("Raw Datar", use_container_width=True):
        st.switch_page(pg_raw)
with col2:
    if st.button("Pump Curves", use_container_width=True):
        st.switch_page(pg_pumps)
with col3:
    if st.button("Demands", use_container_width=True):
        st.switch_page(pg_demand)
with col4:
    if st.button("Water Losses", use_container_width=True):
        st.switch_page(pg_water_losses)
with col5:
    if st.button("Storage", use_container_width=True):
        st.switch_page(pg_storage)


nav.run()