import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px


def water_losses_page():
    st.title("Backwash frequency, volume, duration")

    df = pd.read_csv("data/backwash_plot_data_comprehensive.csv")

    # Ensure timestamps are real datetimes
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["paired_timestamp"] = pd.to_datetime(df["paired_timestamp"])

    events = df[df["data_type"] == "backwash_event"].copy()
    process = df[df["data_type"] == "process_duration"].copy()

    # Build lists of (start, end, volume) pairs
    event_pairs = events[events["event_type"] == "backwash_event_start"][[
        "timestamp", "paired_timestamp", "volume_m3"
    ]]
    duration_pairs = process[process["event_type"] == "process_start"][[
        "timestamp", "paired_timestamp"
    ]]

    # For a neat y-axis limit
    y_max = 1.0 * event_pairs["volume_m3"].max()

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
                    "<b>Phase 1 : Backwash Process Duration</b><br>"
                    "Start : %{customdata[0]|%Y-%m-%d %H:%M}<br>"
                    "End   : %{customdata[1]|%Y-%m-%d %H:%M}"
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
            fillcolor="rgba(153,173,183,0.40)",
            line_width=0,
            layer="below"
        )

    # ---------------- Phase 2 : orange rectangles --------------------------------
    for start, end, vol in event_pairs.itertuples(index=False):
        fig.add_trace(
            go.Scatter(
                x=[start, end], y=[0, vol],
                mode="lines",
                marker=dict(size=20, color="#bf5700"),  # invisible
                customdata=[[start, end]],
                hovertemplate=(
                    "<b>Phase 2 : Backwash Event</b><br>"
                    "Start : %{customdata[0]|%Y-%m-%d %H:%M}<br>"
                    "End   : %{customdata[1]|%Y-%m-%d %H:%M}<br>"
                    "Volume: %{y:.2f} m³"
                    "<extra></extra>"
                ),
                showlegend=False,
                name=""
            )
        )

        fig.add_shape(
            type="rect",
            x0=start, x1=end, y0=0, y1=vol,
            xref="x", yref="y",
            fillcolor="#bf5700",
            line_width=0.1,
            layer="below"
        )

    # ---------------- Dummy traces for legend icons ------------------------------
    fig.add_trace(go.Scatter(
        x=[None], y=[None],
        mode="markers",
        marker=dict(size=10, color="#9cadb7"),
        name="Phase 1 : Backwash Process Duration"
    ))
    fig.add_trace(go.Scatter(
        x=[None], y=[None],
        mode="markers",
        marker=dict(size=10, color="#bf5700"),
        name="Phase 2 : Backwash Event"
    ))

    fig.update_yaxes(
        title_text="Backwash Volume [m³]",
        title_font_size=16,
        range=[0, y_max],
        tickfont_size=16,
    )

    fig.update_xaxes(
        title_text="Date / Time",
        title_font_size=16,
        tickformat="%d %b",
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
    )
    st.plotly_chart(fig, use_container_width=True)
