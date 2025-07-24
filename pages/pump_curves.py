import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def pump_curves_page():
    st.title("Pump Curves")

    data = pd.read_csv("data/flow_head_cluster_data.csv")

    fig = make_subplots(rows=1, cols=2, shared_yaxes=True)
    fig.add_trace(go.Scatter(x=data["Flow_Rate_m3hr"], y=data["Head_m"], mode='markers',
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
    fig.update_xaxes(title="Flow (m^3/hr)", row=1, col=2)
    fig.update_layout(showlegend=False, margin=dict(r=50, l=50), width=500)
    st.plotly_chart(fig, use_container_width=True)