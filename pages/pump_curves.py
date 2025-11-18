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

    resample_hr = st.number_input(r"$\textsf{\Large Aggregation Resolution (Hours):}$",
                                  min_value=1, max_value=24, value=2, step=1, width=300)
    df.index = df['Date']
    df = df.resample(f'{resample_hr}h').first()
    st.text(" ")

    min_d, max_d = df["Date"].min().date(), df["Date"].max().date()
    date_win = st.slider(r"$\textsf{\Large Select window}$", min_value=min_d, max_value=max_d, value=(min_d, max_d))
    st.divider()
    mask = (df["Date"] >= pd.Timestamp(date_win[0])) & (df["Date"] <= pd.Timestamp(date_win[1]))
    dfv = df.loc[mask].copy()

    fig = make_subplots(rows=1, cols=2, subplot_titles=("Pump Curve (Q-H)", "System Pressure (m)"))
    legend_items = {7: 1, 8: 2, 9: 3, 10: 4, 11: 5, 12: 6, 13: 7, 14: 8, 15: 9}
    for cl in df["cluster"].unique():
        sub_all = df[df["cluster"] == cl]  # for legend item spanning full series
        sub_view = dfv[dfv["cluster"] == cl]  # respects selected date window

        if sub_all.empty:
            continue

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
    fig.update_yaxes(title_text="System Pressure (PSI)", row=1, col=2)
    fig.update_xaxes(title_text="Flow Rate (GPM)", row=1, col=2)
    fig.update_yaxes(title_text="Pump Head (ft)", row=1, col=1)
    fig.update_layout(legend_title_text="Clusters", height=480, margin=dict(l=10, r=10, t=20, b=20))

    fig.update_xaxes(tickfont=dict(size=utils.GRAPHS_FONT_SIZE))
    fig.update_yaxes(tickfont=dict(size=utils.GRAPHS_FONT_SIZE))
    fig.update_xaxes(title_font=dict(size=utils.GRAPHS_FONT_SIZE))
    fig.update_yaxes(title_font=dict(size=utils.GRAPHS_FONT_SIZE))
    fig.update_annotations(font=dict(size=utils.GRAPHS_FONT_SIZE))
    st.plotly_chart(fig, use_container_width=True)

    st.divider()

    q_scale = df["flow_gpm"].max() - df["flow_gpm"].min()
    h_scale = df["pressure_psi"].max() - df["pressure_psi"].min()

    X = np.column_stack([
        (df["flow_gpm"].to_numpy() / q_scale),
        (df["pressure_psi"].to_numpy() / h_scale),
    ])
    clusters = df["cluster"].to_numpy()

    def predict_cluster_knn(q, h, k=5):
        qn = q / q_scale
        hn = h / h_scale
        diff = X - np.array([qn, hn])
        dist2 = np.sum(diff ** 2, axis=1)
        idx_sorted = np.argsort(dist2)[:k]
        # majority vote among nearest k clusters
        nearest_clusters = clusters[idx_sorted]
        values, counts = np.unique(nearest_clusters, return_counts=True)
        majority_cluster = values[counts.argmax()]
        # also return the closest point for info
        closest_idx = idx_sorted[0]
        return majority_cluster, df.iloc[closest_idx]

    col1, col2, col3, spacer = st.columns([1, 1, 1, 0.2])
    with col1:
        q = st.number_input("Q (GPM)", min_value=0.0, max_value=65.0, value=45.0, key="q_input")
    with col2:
        h = st.number_input("H (PSI)", min_value=1.0, max_value=15.0, value=7.0, key="h_input")
    with col3:
        try:
            cluster, point_info = predict_cluster_knn(q, h, k=3)
            st.metric("Required Speed Cluster", legend_items[int(cluster)])
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
