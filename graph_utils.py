import os
import sys
import pandas as pd
import streamlit as st
from typing import List
import plotly.graph_objects as go
from plotly.subplots import make_subplots

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BAR_COLORS = ["#223b9f", "#a0d7f4", "#fad06c", "#f74013"]
COLORS = ["#2050b8", "#6bc3f7", "#0e8a8c", "#94d2bd", "#e9d8a6", "#f0b64a", "#f5912e", "#ee350c", "#a91a0d", "#f79fee"]
# COLORS = [blue, light blue, Teal, light green, light orange, orange, dark orange, red, dark red, pink]


def plot_time_series(
        data: pd.DataFrame,
        data_col_names: List[str] | None = None,    # optional column name for single-column data
        line_kw: dict | None = None,                # forwarded to fig.add_trace()
        height_single: int = 200,                   # px for a single chart
):

    data.index = pd.to_datetime(data.index)  # ensure index is datetime-like

    if data_col_names is not None:
        cols = data_col_names
    else:
        cols = data.columns.tolist()

    if len(cols) > 1:
        fig = make_subplots(rows=len(cols), cols=1, shared_xaxes=True, vertical_spacing=0.1)
        for i, col in enumerate(cols, start=1):
            fig.add_trace(go.Scatter(x=data.index, y=data[col], name=col, line=dict(color=COLORS[0]), **line_kw),
                          row=i, col=1)
            fig.update_yaxes(title=col, secondary_y=False, row=i, col=1)
        fig.update_layout(height=height_single * len(cols))
        # fig.update_xaxes(rangeslider={'visible': False, "bordercolor": "black", "borderwidth": 1},
        #                  row=len(cols), col=1, rangeslider_thickness=0.1)

    else:
        fig = make_subplots(rows=1, cols=1, shared_xaxes=True, vertical_spacing=0.1)
        for col in cols:
            fig.add_trace(go.Scatter(x=data.index, y=data[col], zorder=5, **line_kw))
            fig.update_yaxes(title=col, secondary_y=False, row=1, col=1)
        fig.update_layout(height=height_single*2.5)
        fig.update_xaxes(rangeslider={'visible': True, "bordercolor": "black", "borderwidth": 1},
                         row=len(cols), col=1, rangeslider_thickness=0.18)

    fig.update_layout(showlegend=False, margin=dict(r=50, l=50))
    return fig


