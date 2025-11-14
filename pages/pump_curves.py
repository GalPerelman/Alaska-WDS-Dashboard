import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots

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
    df = pd.read_csv("data/2_pump curves/pressure_pump_curves.csv")

    # Filter clusters with at least 10 points
    df = df[df.groupby("cluster")["cluster"].transform("count") >= 10]

    # Assign colors to clusters
    unique_clusters = sorted(df["cluster"].unique())
    color_map = {c: graph_utils.COLORS[i % len(unique_clusters)] for i, c in enumerate(unique_clusters)}
    df["color"] = df["cluster"].map(color_map)

    # Change units
    df["flow_gpm"] = df["Master Meter Flow Rate_m3hr"] * 4.40287  # m3/hr to GPM
    df["pressure_psi"] = df["Distribution System Pressure Head, m"] * 0.433514  # m to psi
    return df


def pump_curves_page():
    st.title("Pump Curves")

    data = pd.read_csv("data/flow_head_cluster_data.csv")

    df = preprocess()
    df["Date"] = df["Timestamp"]
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.sort_values(["Date", "cluster"])

    min_d, max_d = df["Date"].min().date(), df["Date"].max().date()
    date_win = st.slider(r"$\textsf{\Large Select window}$", min_value=min_d, max_value=max_d, value=(min_d, max_d))
    st.divider()
    mask = (df["Date"] >= pd.Timestamp(date_win[0])) & (df["Date"] <= pd.Timestamp(date_win[1]))
    dfv = df.loc[mask].copy()

    fig = make_subplots(rows=1, cols=2, subplot_titles=("System Pressure (m)", "Pump Curve (Q-H)"))
    legend_items = {7: 1, 8: 2, 9: 3, 10: 4, 11: 5, 12: 6, 13: 7, 14: 8, 15: 9}
    for cl in df["cluster"].unique():
        sub_all = df[df["cluster"] == cl]  # for legend item spanning full series
        sub_view = dfv[dfv["cluster"] == cl]  # respects selected date window

        color = sub_all["color"].iloc[0]
        llegend_label = f"cluster-{legend_items[int(cl)]}"  # legend group name

        # left: pump curve
        fig.add_trace(
            go.Scatter(
                x=sub_view["flow_gpm"], y=sub_view["pressure_psi"],
                mode="markers",
                marker=dict(color=color, size=8, line=dict(width=0.2, color="DarkSlateGrey")),
                name=f"Cluster {legend_items[int(cl)]}",
                legendgroup=llegend_label,
                showlegend=False
            ),
            row=1, col=1
        )

        # Right: time series
        fig.add_trace(
            go.Scatter(
                x=sub_view["Date"], y=sub_view["pressure_psi"],
                mode="markers",
                marker=dict(color=color, size=8, line=dict(width=0.2, color="DarkSlateGrey")),
                name=f"Cluster {legend_items[int(cl)]}",
                legendgroup=llegend_label,
                showlegend=True,
                legendrank=legend_items[cl]
            ),
            row=1, col=2,
        )

    fig.update_xaxes(title_text="Date", row=1, col=1)
    fig.update_yaxes(title_text="System Pressure (PSI)", row=1, col=1)
    fig.update_xaxes(title_text="Flow Rate (GPM)", row=1, col=2)
    fig.update_yaxes(title_text="Pump Head (PSI)", row=1, col=2)
    fig.update_layout(legend_title_text="Clusters", height=480, margin=dict(l=10, r=10, t=20, b=20))

    fig.update_xaxes(tickfont=dict(size=utils.GRAPHS_FONT_SIZE))
    fig.update_yaxes(tickfont=dict(size=utils.GRAPHS_FONT_SIZE))
    fig.update_xaxes(title_font=dict(size=utils.GRAPHS_FONT_SIZE))
    fig.update_yaxes(title_font=dict(size=utils.GRAPHS_FONT_SIZE))
    fig.update_annotations(font=dict(size=utils.GRAPHS_FONT_SIZE))
    st.plotly_chart(fig, use_container_width=True)

    st.divider()
    col1, col2, col3, spacer = st.columns([1, 1, 1, 0.2])
    with col1:
        q = st.number_input("Q (GPM)", min_value=0.0, max_value=65.0, value=50.0, key="q_input")
    with col2:
        h = st.number_input("H (PSI)", min_value=6.0, max_value=11.0, value=8.0, key="h_input")
    with col3:
        st.metric("Required Pump Speed", q + h)