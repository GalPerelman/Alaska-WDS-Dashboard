import pandas as pd
import streamlit as st
from PIL import Image

import graph_utils
import utils

def raw_data_page():
    st.title("Raw Data")

    treated_flow = pd.read_csv("data/1_raw sensor data/1_treated_water.csv", index_col=0, parse_dates=True)
    tank = pd.read_csv("data/1_raw sensor data/2_tank_water_level.csv", index_col=0, parse_dates=True)
    system_flow = pd.read_csv("data/1_raw sensor data/3_system_flow.csv", index_col=0, parse_dates=True)
    pressure = pd.read_csv("data/1_raw sensor data/4_system_pressure.csv", index_col=0, parse_dates=True)

    data = pd.concat([
        treated_flow["Filtered Water Flow Rate, GPM"].rename("Treated Flow<br>(GPM)"),
        tank["WST Height, ft"].rename("Tank Level<br>(ft)"),
        system_flow["Master Meter Flow Rate, GPM"].rename("System Flow<br>(GPM)"),
        pressure["Distribution System Pressure, psi"].rename("System Pressure<br>(PSI)"),
                          ], axis=1)

    data["Date"] = data.index
    data["Date"] = pd.to_datetime(data["Date"])
    min_d, max_d = data["Date"].min().date(), data["Date"].max().date()
    date_win = st.slider(r"$\textsf{\Large Select window}$", min_value=min_d, max_value=max_d, value=(min_d, max_d))
    st.divider()
    mask = (data["Date"] >= pd.Timestamp(date_win[0])) & (data["Date"] <= pd.Timestamp(date_win[1]))
    filtered_data = data.loc[mask].copy().drop(columns=["Date"])

    st.text(" ")
    st.markdown("""
        <span style='
            font-size: 24px;
            margin-top: 0; 
        '>
        Timestamps are according to Alaska Standard Time.
        </span>
        """, unsafe_allow_html=True)
    st.text(" ")

    fig = graph_utils.plot_time_series(
        data=filtered_data,
        height_single=350,
        vertical_spacing=0.1,
        line_kw=dict(line_width=1.6))

    # customized the y limits of the last plot - artifically ignore outlier
    fig.update_yaxes(range=[0, 100], row=4, col=1)
    fig.update_layout(margin=dict(t=0))
    st.plotly_chart(fig)

    st.text(" ")
    st.text(" ")
    st.divider()

    target_height = 250
    img1 = Image.open("resources/1_treated_flow_sensor.jpg")
    img2 = Image.open("resources/2_demand_sensor.jpg")
    img3 = Image.open("resources/3_tank_level_sensor.jpg")
    img4 = Image.open("resources/4_pressure_sensor.jpg")
    img1_resized = utils.resize_to_height(img1, target_height)
    img2_resized = utils.resize_to_height(img2, target_height)
    img3_resized = utils.resize_to_height(img3, target_height)
    img4_resized = utils.resize_to_height(img4, target_height)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.image(img1_resized, caption="Treated Water Flow Rate Meter")
    with col2:
        st.image(img2_resized, caption="System Flow Meter")
    with col3:
        st.image(img3_resized, caption="Tank Water Level Sensor")
    with col4:
        st.image(img4_resized, caption="System Pressure Sensor")