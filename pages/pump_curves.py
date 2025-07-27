import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def pump_curves_page():
    st.title("Pump Curves")

    data = pd.read_csv("data/flow_head_cluster_data.csv")

    fig = make_subplots(rows=1, cols=2, shared_yaxes=True)
    fig.add_trace(go.Scatter(x=data["Flow_Rate_m3hr"], y=data["Head_m"], mode='markers',
                             marker=dict(color="#f8971f"),
                             hovertemplate="Q = %{x:.2f} m³/h<br>H = %{y:.2f} m<extra></extra>"), row=1, col=1)
    fig.update_yaxes(title="Head (m)", row=1, col=1)
    fig.update_xaxes(title="Flow (m^3/hr)", row=1, col=1)

    fig.add_trace(go.Scatter(x=data["Flow_Rate_m3hr"], y=data["Head_m"], mode='markers',
                             marker=dict(color=data["Cluster_Color"]),
                             text=data["Cluster_Label"],
                             hovertemplate="Q = %{x:.2f} m³/h<br>H = %{y:.2f} m<br>Cluster = %{text}<extra></extra>"),
                  row=1, col=2,
                  )
    fig.update_yaxes(title="Head (m)", secondary_y=False, row=1, col=2)
    fig.update_xaxes(title="Flow (m³/hr)", row=1, col=2)
    fig.update_layout(showlegend=False, margin=dict(r=50, l=50), width=500)

    col1, spacer = st.columns([1, 0.2])
    with col1:
        st.plotly_chart(fig, use_container_width=True)

    st.text("\n")

    # Pump Curves Time Series Clusters
    data = pd.read_csv("data/time_series_cluster_data.csv")  # replace with pd.read_csv("file.csv")
    data["Date"] = pd.to_datetime(data["Date"])
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

    fig = go.Figure()
    for label, g in data.groupby("Cluster_Label"):
        symbol = symbol_map.get(g["Cluster_Shape"].iloc[0], "circle")
        color = g["Cluster_Color"].iloc[0]

        fig.add_trace(
            go.Scatter(
                x=g["Date"],
                y=g["System_Pressure_m"],
                mode="markers",
                name=f"Cluster {label}",
                marker=dict(
                    symbol=symbol,
                    color=color,
                    size=12,  # scale to taste
                    line=dict(width=0)  # no marker outline
                ),
                customdata=g[["Flow_Rate_m3hr", "Pump_Head_m"]],  # used in hovertemplate
                hovertemplate=(
                    "Flow [m³/hr]: %{customdata[0]:.2f}<br>"
                    "System Pressure [m]: %{y:.2f}<br>"
                    "Pump Head [m]: %{customdata[1]:.2f}<br>"
                    "Cluster: %{text}</b>"
                ),
                text=[label] * len(g)  # used in hovertemplate
            )
        )

    fig.update_layout(
        template="simple_white",
        font=dict(size=18),
        margin=dict(l=80, r=60, t=20, b=80)
    )

    fig.update_xaxes(
        title_text="Time",
        title_font_size=16,
        tickfont_size=14,
    )
    fig.update_yaxes(
        title_text="System Pressure (m)",
        title_font_size=16,
        tickfont_size=14,
    )

    col1, spacer = st.columns([1, 0.2])
    with col1:
        st.plotly_chart(fig, use_container_width=True)