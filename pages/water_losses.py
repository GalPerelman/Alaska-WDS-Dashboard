import pandas as pd
import streamlit as st
import plotly.graph_objects as go

import utils

ORANGE = "#bf5700"
GREY = "#c8cacc"


def water_losses_page():
    st.title("Backwash frequency, volume, duration")

    df = pd.read_csv("data/backwash_plot_data_comprehensive.csv")

    df["Date"] = df["timestamp"]
    df["Date"] = pd.to_datetime(df["Date"])
    min_d, max_d = df["Date"].min().date(), df["Date"].max().date()
    date_win = st.slider(r"$\textsf{\Large Select window}$", min_value=min_d, max_value=max_d, value=(min_d, max_d))
    st.divider()
    mask = (df["Date"] >= pd.Timestamp(date_win[0])) & (df["Date"] <= pd.Timestamp(date_win[1]))
    df = df.loc[mask].copy()

    # Ensure timestamps are real datetimes
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["paired_timestamp"] = pd.to_datetime(df["paired_timestamp"])

    df["volume_ft3"] = df["volume_m3"] * 35.3147  # m3 to ft3

    events = df[df["data_type"] == "backwash_event"].copy()
    process = df[df["data_type"] == "process_duration"].copy()

    # Build lists of (start, end, volume) pairs
    event_pairs = events[events["event_type"] == "backwash_event_start"][[
        "timestamp", "paired_timestamp", "volume_ft3"
    ]]
    duration_pairs = process[process["event_type"] == "process_start"][[
        "timestamp", "paired_timestamp"
    ]]

    # For a neat y-axis limit
    y_max = 1.0 * event_pairs["volume_ft3"].max()

    fig = go.Figure()
    # ---------------- Phase 1 : grey background spans ----------------------------
    for start, end in duration_pairs.itertuples(index=False):
        # --- draw the grey band as a SHAPE (no change) -------------------------
        fig.add_trace(
            go.Scatter(
                x=[start], y=[y_max],
                mode="lines",
                marker=dict(size=20, color="rgba(0,0,0,0)"),  # invisible
                customdata=[[start, end]],
                hovertemplate=(
                    f"<span style='color:{GREY};'>"
                    "<b>Phase 1 : Backwash Process Duration</b><br>"
                    "Start : %{customdata[0]|%Y-%m-%d %H:%M}<br>"
                    "End   : %{customdata[1]|%Y-%m-%d %H:%M}"
                    "</span>"
                    "<extra></extra>"

                ),
                showlegend=False,
                name=""
            )
        )

        fig.add_shape(
            type="rect",
            x0=start, x1=end, y0=0, y1=y_max,
            xref="x", yref="y",
            fillcolor=GREY,
            line_width=0,
            layer="below"
        )

    # ---------------- Phase 2 : orange rectangles --------------------------------
    hover_x = []
    hover_y = []
    hover_cd = []
    line_x = []
    line_y = []
    for start, end, vol in event_pairs.itertuples(index=False):
        # 1) true-duration orange rectangle as a shape
        fig.add_shape(
            type="rect",
            x0=start, x1=end, y0=0, y1=vol,
            xref="x", yref="y",
            fillcolor=ORANGE,
            line_width=0,
            layer="below"
        )

        # 2) a visible vertical line at the event start (pixel-wide, easy to see)
        line_x.extend([start, start, None])  # None breaks the segment between events
        line_y.extend([0, vol, None])

        # 3) invisible hover marker at the midpoint (for nice tooltips)
        mid = start + (end - start) / 2
        hover_x.append(mid)
        hover_y.append(vol)  # doesn’t matter much; we use customdata
        hover_cd.append([start, end, vol])

    # trace for visible orange lines (no hover)
    fig.add_trace(
        go.Scatter(
            x=line_x,
            y=line_y,
            mode="lines",
            line=dict(color=ORANGE, width=2.5),
            hoverinfo="skip",  # <– no hover from these, only for visual
            showlegend=False,
            name=""
        )
    )

    # trace for hover only (invisible markers)
    fig.add_trace(
        go.Scatter(
            x=hover_x,
            y=hover_y,
            mode="markers",
            marker=dict(size=20, color="rgba(0,0,0,0)"),  # invisible
            customdata=hover_cd,
            hovertemplate=(
                f"<span style='color:{ORANGE};'>"
                "<b>Phase 2 : Backwash Event</b><br>"
                "Start : %{customdata[0]|%Y-%m-%d %H:%M}<br>"
                "End   : %{customdata[1]|%Y-%m-%d %H:%M}<br>"
                "Volume: %{customdata[2]:.2f} m³"
                "</span>"
                "<extra></extra>"
            ),
            showlegend=False,
            name=""
        )
    )

    # ---------------- Dummy traces for legend icons ------------------------------
    fig.add_trace(go.Scatter(
        x=[None], y=[None],
        mode="markers",
        marker=dict(size=10, color=GREY),
        name="Phase 1 : Backwash Process Duration"
    ))
    fig.add_trace(go.Scatter(
        x=[None], y=[None],
        mode="markers",
        marker=dict(size=10, color=ORANGE),
        name="Phase 2 : Backwash Event"
    ))

    fig.update_yaxes(
        title_text="Backwash Volume (ft³)",
        title_font_size=16,
        range=[0, y_max],
        tickfont_size=16,
    )

    fig.update_xaxes(
        title_text="Date",
        title_font_size=16,
        tickfont_size=16,
    )

    fig.update_layout(
        font=dict(size=16),
        height=500,
        legend=dict(
            orientation="h",
            yanchor="bottom", y=1.02,
            xanchor="left", x=0,
            font=dict(size=14)
        ),
        margin=dict(l=80, r=40, t=80, b=60),
        hovermode="x",
        yaxis=dict(showgrid=False)
    )

    fig.update_xaxes(tickfont=dict(size=utils.GRAPHS_FONT_SIZE))
    fig.update_yaxes(tickfont=dict(size=utils.GRAPHS_FONT_SIZE))
    fig.update_xaxes(title_font=dict(size=utils.GRAPHS_FONT_SIZE))
    fig.update_yaxes(title_font=dict(size=utils.GRAPHS_FONT_SIZE))
    st.plotly_chart(fig, use_container_width=True)
