import os
import sys
import pandas as pd

from typing import List
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px

import utils

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

COLORS = (["#0F6CB3", "#48ad90", "#6fcfec", "#f3ebb8", "#ade0a3", "#e7d18f", "#7ccb97", "#AAD0EE", "#27787c", "#229bd3"]
          + ["#adffe8", "#72efdd", "#67e0e0", "#63d2e3", "#21aad4", "#79a8e2", "#8284d9", "#966cda", "#7400b8"]
          + px.colors.qualitative.Plotly
          + px.colors.qualitative.D3
          + px.colors.qualitative.G10
          + px.colors.qualitative.T10
          + px.colors.qualitative.Prism
          )

BAR_COLORS = [COLORS[0], COLORS[1], COLORS[2], COLORS[3]]


def plot_time_series(
        data: pd.DataFrame,
        data_col_names: List[str] | None = None,    # optional column name for single-column data
        line_kw: dict | None = None,                # forwarded to fig.add_trace()
        height_single: int = 250,                   # px for a single chart
        vertical_spacing=0.15,
        sharex=False,
        same_color=False,
        range_slider=False
):

    data.index = pd.to_datetime(data.index)  # ensure index is datetime-like

    if data_col_names is not None:
        cols = data_col_names
    else:
        cols = data.columns.tolist()

    if same_color:
        plot_colors = [COLORS[0] for _ in cols]
    else:
        plot_colors = COLORS[:len(cols)+1]

    if len(cols) > 1:
        fig = make_subplots(rows=len(cols), cols=1, shared_xaxes=sharex, vertical_spacing=0.15)
        for i, col in enumerate(cols, start=1):
            fig.add_trace(go.Scatter(x=data.index, y=data[col], name=col, line=dict(color=plot_colors[i]), **line_kw),
                          row=i, col=1)
            fig.update_yaxes(title=col, secondary_y=False, row=i, col=1)
        fig.update_layout(height=height_single * len(cols))
        # fig.update_xaxes(rangeslider={'visible': False, "bordercolor": "black", "borderwidth": 1},
        #                  row=len(cols), col=1, rangeslider_thickness=0.1)

    else:
        fig = make_subplots(rows=1, cols=1, shared_xaxes=sharex, vertical_spacing=0.1)
        for i, col in enumerate(cols):
            fig.add_trace(go.Scatter(x=data.index, y=data[col], zorder=5, line=dict(color=plot_colors[0]), **line_kw))
            fig.update_yaxes(title=col, secondary_y=False, row=1, col=1)
        fig.update_layout(height=height_single*2.5)
        if range_slider:
            fig.update_xaxes(rangeslider={'visible': True, "bordercolor": "black", "borderwidth": 1},
                             row=len(cols), col=1, rangeslider_thickness=0.18)

    fig.update_layout(showlegend=False, margin=dict(r=50, l=50))
    fig.update_xaxes(tickfont=dict(size=utils.GRAPHS_FONT_SIZE))
    fig.update_yaxes(tickfont=dict(size=utils.GRAPHS_FONT_SIZE))
    fig.update_xaxes(title_font=dict(size=utils.GRAPHS_FONT_SIZE))
    fig.update_yaxes(title_font=dict(size=utils.GRAPHS_FONT_SIZE))
    return fig


