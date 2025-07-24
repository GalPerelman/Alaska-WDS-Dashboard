import pandas as pd
import streamlit as st

import graph_utils


def raw_data_page():
    st.title("Raw Data")
    st.text(" ")

    raw_data = pd.read_csv("data/raw_timeseries_data.csv", index_col=0)

    fig = graph_utils.plot_time_series(
        data=raw_data,
        line_kw=dict(line_width=1.6))
    st.plotly_chart(fig)