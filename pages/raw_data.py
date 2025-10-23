import pandas as pd
import streamlit as st

import graph_utils


def raw_data_page():
    st.title("Raw Data")
    st.text(" ")

    raw_data = pd.read_csv("data/raw_timeseries_data.csv", index_col=0)

    treated_flow = pd.read_csv("data/1_raw sensor data/1_treated_water.csv", index_col=0, parse_dates=True)
    tank = pd.read_csv("data/1_raw sensor data/2_tank_water_level.csv", index_col=0, parse_dates=True)
    system_flow = pd.read_csv("data/1_raw sensor data/3_system_flow.csv", index_col=0, parse_dates=True)
    pressure = pd.read_csv("data/1_raw sensor data/4_system_pressure.csv", index_col=0, parse_dates=True)

    raw_data = pd.concat([
        treated_flow["Filtered Water Flow Rate, GPM"].rename("Treated Flow<br>(GPM)"),
        tank["WST Height, ft"].rename("Tank Level<br>(ft)"),
        system_flow["Master Meter Flow Rate, GPM"].rename("System Flow<br>(GPM)"),
        pressure["Distribution System Pressure, psi"].rename("System Pressure<br>(PSI)"),
                          ], axis=1)

    fig = graph_utils.plot_time_series(
        data=raw_data,
        line_kw=dict(line_width=1.6))
    st.plotly_chart(fig)