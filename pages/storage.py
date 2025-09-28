import pandas as pd
import streamlit as st
import plotly.express as px

import graph_utils


def storage_page():
    st.title("Storage Level")

    data = pd.read_csv("data/Arctic Village_water_level_data.csv", index_col=0)
    data["water_level_ft"] = data["water_level_m"] * 3.28084  # m to ft
    data["critical_threshold_ft"] = data["critical_threshold_m"] * 3.28084  # m to ft
    fig = graph_utils.plot_time_series(
        data=data,
        data_col_names=["water_level_ft"],
        line_kw=dict(line_width=1.6))

    threshold = data["critical_threshold_ft"].iloc[0]
    fig.add_hline(
        y=threshold,
        line=dict(color="red", dash="dash"),
        annotation_text=f"Critical ({threshold:.2f} ft)",
        annotation_position="top left",
        annotation_font_color="red",
    )

    # Identify contiguous True stretches
    # Every time the mask flips (True to False or False to True) we start a new group
    mask = data["water_level_ft"] < threshold
    data["group"] = (mask != mask.shift()).cumsum()

    violation_ranges = (
        data.loc[mask]
        .groupby("group")
        .apply(lambda g: pd.Series({
            "x0": g.index[0],  # first timestamp in the group
            "x1": g.index[-1]  # last  timestamp in the group
        }))
    )

    for _, row in violation_ranges.iterrows():
        fig.add_shape(
            type="rect",
            x0=row.x0, x1=row.x1,
            xref="x",
            y0=0, y1=1,
            yref="paper",  # 0–1 = full vertical span
            fillcolor="grey",  # translucent red
            line_width=0,
            opacity=0.3,
            layer="below"
        )

    fig.update_xaxes(
        title_text="Time",
        title_font_size=16,
        tickfont_size=14,
    )
    fig.update_yaxes(
        title_text="Water Level (ft)",
        title_font_size=16,
        tickfont_size=16,
    )

    fig.update_layout(
        hovermode="x unified"
    )
    st.plotly_chart(fig)