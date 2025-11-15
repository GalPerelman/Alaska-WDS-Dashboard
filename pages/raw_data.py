import pandas as pd
import streamlit as st

import graph_utils


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
            font-size: 20px;
            margin-top: 0; 
        '>
        Timestamps are according to Alaska Standard Time.
        </span>
        """, unsafe_allow_html=True)

    fig = graph_utils.plot_time_series(
        data=filtered_data,
        line_kw=dict(line_width=1.6))
    st.plotly_chart(fig)