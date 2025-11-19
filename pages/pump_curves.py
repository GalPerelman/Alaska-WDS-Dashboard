import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from PIL import Image

import graph_utils
import utils

symbol_map = {
            "*": "star",
            "v": "triangle-down",
            "^": "triangle-up",
            "o": "circle",
            "s": "square",
            "d": "diamond",
            "+": "cross",
            "x": "x"
        }


def preprocess():
    df = pd.read_csv("data/2_pump curves/pressure_pump_curves.csv", index_col=0)

    # Filter clusters with at least 10 points
    df = df[df.groupby("cluster")["cluster"].transform("count") >= 10]

    # Change units
    df["flow_gpm"] = df["Master Meter Flow Rate_m3hr"] * 4.40287  # m3/hr to GPM
    df["pressure_psi"] = df["Distribution System Pressure Head, psi"]
    return df


def pump_curves_page():
    st.title("Pump Curves")

    df = preprocess()
    df["Date"] = df["Timestamp"]
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.sort_values(["Date", "cluster"])

    # this allows the user to select aggregation resolution, removed for now
    # resample_hr = st.number_input(r"$\textsf{\Large Aggregation Resolution (Hours):}$",
    #                               min_value=1, max_value=24, value=2, step=1, width=300)
    resample_hr = 1
    df.index = df['Date']

    df = df.resample(f'{resample_hr}h').first()
    df = df.dropna(subset=["cluster"])  # the aggregation may produce NaNs
    st.text(" ")

    min_d, max_d = df["Date"].min().date(), df["Date"].max().date()
    date_win = st.slider(r"$\textsf{\Large Select window}$", min_value=min_d, max_value=max_d, value=(min_d, max_d))
    st.divider()
    mask = (df["Date"] >= pd.Timestamp(date_win[0])) & (df["Date"] <= pd.Timestamp(date_win[1]))
    dfv = df.loc[mask].copy()

    fig = make_subplots(rows=1, cols=2, subplot_titles=("Pump Curve (Q-H)", "System Pressure (PSI)"),
                        column_widths=[0.65, 0.35])
    legend_items = {7: 1, 8: 2, 9: 3, 10: 4, 11: 5, 12: 6, 13: 7, 14: 8, 15: 9}
    for i, cl in enumerate(df["cluster"].unique()):
        sub_all = df[df["cluster"] == cl]  # for legend item spanning full series
        sub_view = dfv[dfv["cluster"] == cl]  # respects selected date window

        ts_sub_view = sub_view.resample('ME').first()

        if sub_all.empty:
            continue

        color = graph_utils.COLORS[i]
        llegend_label = f"cluster-{legend_items[int(cl)]}"  # legend group name

        # left: pump curve
        fig.add_trace(
            go.Scatter(
                x=sub_view["flow_gpm"], y=sub_view["pump_head_ft"],
                mode="markers",
                marker=dict(color=color, size=6, line=dict(width=0.2, color="DarkSlateGrey")),
                name=f"Cluster {legend_items[int(cl)]}",
                legendgroup=llegend_label,
                showlegend=False
            ),
            row=1, col=1
        )

        # Right: time series
        fig.add_trace(
            go.Scatter(
                x=ts_sub_view["Date"], y=ts_sub_view["pressure_psi"],
                mode="markers",
                marker=dict(color=color, size=6, line=dict(width=0.2, color="DarkSlateGrey")),
                name=f"Cluster {legend_items[int(cl)]}",
                legendgroup=llegend_label,
                showlegend=True,
                legendrank=legend_items[int(cl)]
            ),
            row=1, col=2,
        )

    fig.update_xaxes(title_text="Flow Rate (GPM)", row=1, col=1)
    fig.update_yaxes(title_text="Pump Head (ft)", row=1, col=1)

    fig.update_xaxes(title_text="Date", row=1, col=2)
    fig.update_yaxes(title_text="System Pressure (PSI)", row=1, col=2)

    fig.update_layout(height=600)
    fig.update_layout(
        legend=dict(
            orientation="h",  # Set legend orientation to horizontal
            xanchor="center",  # Anchor the legend's horizontal position to its center
            x=0.5,  # Position the legend horizontally at the center of the figure
            y=-0.4  # Position the legend vertically below the plot area
        )
    )
    fig.update_layout(margin=dict(l=10, r=10, t=50, b=1))

    fig.update_xaxes(tickfont=dict(size=utils.GRAPHS_FONT_SIZE))
    fig.update_yaxes(tickfont=dict(size=utils.GRAPHS_FONT_SIZE))
    fig.update_xaxes(title_font=dict(size=utils.GRAPHS_FONT_SIZE))
    fig.update_yaxes(title_font=dict(size=utils.GRAPHS_FONT_SIZE))
    fig.update_annotations(font=dict(size=utils.GRAPHS_FONT_SIZE))
    st.plotly_chart(fig, use_container_width=True)

    st.divider()

    curves = pd.DataFrame({'a': [-0.006755334, -0.006755334, -0.006755334, -0.006755334, -0.006755334, -0.006755334,
                                 -0.006755334, -0.006755334, -0.006755334
                                 ],
                           'b': [0.306215982, 0.322547501, 0.33887902, 0.355210539, 0.371542058, 0.387873577,
                                 0.404205096, 0.420536615, 0.436868135
                                 ],
                           'c': [31.18835733, 34.60382899, 38.19672776, 41.96705362, 45.91480658, 50.03998664,
                                 54.34259381, 58.82262807, 63.48008943
                                 ],
                           'cluster': [7, 8, 9, 10, 11, 12, 13, 14, 15]})

    def hard_coded_curves_pred(q, p, l):
        target_pressure_head = p * 2.31  # psi to ft
        curves['estimated_head'] = curves['a'] * (q ** 2) + curves['b'] * q + curves['c']
        calculated_required_head = target_pressure_head - l
        curves['adjusted_head'] = abs(curves['estimated_head'] - calculated_required_head)
        min_index = curves['adjusted_head'].idxmin()
        closest_curve = curves.loc[min_index, 'cluster']

        return closest_curve

    st.text("Enter the system flow rate and target system pressure to get an operating pump curve")

    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
    with col1:
        q = st.number_input("Flow (GPM)", min_value=0.0, max_value=65.0, value=50.0, key="q_input", step=0.1)
    with col2:
        p = st.number_input("Desired System Pressure (PSI)", min_value=0.0, max_value=100.0, value=32.0, key="p_input",
                            step=0.1)
    with col3:
        l = st.number_input("Tank Level (ft)", min_value=0.0, max_value=22.0, value=20.0, key="l_input", step=0.1)
    with col4:
        try:
            cluster = hard_coded_curves_pred(q, p, l)
            display_label = legend_items[int(cluster)]
            st.metric("Required Speed Cluster", display_label)
        except Exception as e:
            st.error(f"Error in prediction: {e}")

    st.text(" ")
    st.text(" ")
    st.text(" ")
    st.text(" ")

    target_height = 400
    img1 = Image.open("resources/5_pumps.jpg")
    img2 = Image.open("resources/6_pump_speed_change.jpg")
    img1_resized = utils.resize_to_height(img1, target_height)
    img2_resized = utils.resize_to_height(img2, target_height)

    col1, col2, col3, col4 = st.columns(4)
    with col2:
        st.image(img1_resized, caption="System Pumps")
    with col3:
        st.image(img2_resized, caption="Speed Control Panel")
