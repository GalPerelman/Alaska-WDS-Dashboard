import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

import graph_utils

WEEKDAY_COLORS = {"Monday": "#00a9b7", "Tuesday": "#f8971f", "Wednesday": "#9cadb7", "Thursday": "#bf5700",
                  "Friday": "purple", "Saturday": "brown", "Sunday": "pink"}


def demands_page():
    st.title("Demand Patterns")

    data = pd.read_csv("data/median_demand_plotted_points.csv")  # replace with pd.read_csv("file.csv")
    data["time_dt"] = pd.to_datetime("2000-01-01 " + data["time"])  # dummy date

    dow_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    fig = px.scatter(
        data,
        x="time_dt",
        y="median_demand_m3_hr",
        color="day_of_week",
        category_orders={"day_of_week": dow_order},
        color_discrete_sequence=list(WEEKDAY_COLORS.values()),
        custom_data=["day_of_week"]
    )

    fig.update_traces(hovertemplate=(
            "<b>%{customdata[0]}</b><br>"  # day of week
            "Time: %{x|%H:%M}<br>"
            "Demand: %{y:.2f} m³/hr<br>"
            "<extra></extra>"
        ),
        selector=dict(mode="markers"),
    )

    fig.update_traces(marker=dict(size=8, opacity=0.9), selector=dict(mode="markers"))
    # one tick every 3 h  (1 h = 3 600 000 ms)
    fig.update_xaxes(title_text="Time of Day", tickformat="%H:%M", dtick=3_600_000 * 3)

    fig.update_yaxes(title_text="Demand (m³/hr)")
    fig.update_layout(
        legend_title_text="",
        font=dict(size=18, color='black'),
        width=300,
        height=450,
        margin=dict(l=80, r=100, t=40, b=60),
    )

    col1, spacer = st.columns([1, 0.2])
    with col1:
        st.plotly_chart(fig, use_container_width=True)

    # Demands Anomalies
    st.text("\n")
    st.title("Demand Drift Detection")
    data = pd.read_csv("data/real_time_results.csv", index_col=0)
    fig = graph_utils.plot_time_series(
        data=data,
        data_col_names=["Flow (m³/hr)"],
        line_kw=dict(line_width=1.6))

    flag_col = "Is_Event"  # <── the Boolean that drives the shading
    series_col = "Flow (m³/hr)"  # what you want to plot
    color_when_on = "grey"  # translucent orange
    color_when_off = "rgba(0,0,0,0.0)"  # pale blue  (optional)

    mask = data["Is_Event"].astype(bool)  # make sure we have dtype=bool
    data["group"] = (mask != mask.shift()).cumsum()

    intervals = (
        data.groupby("group")
        .apply(lambda g: pd.Series({
            "x0": g.index[0],
            "x1": g.index[-1],
            "flag": g[flag_col].iloc[0]
        }))
    )
    ymin = data[series_col].min()
    ymax = data[series_col].max()
    for _, row in intervals.iterrows():
        if not row.flag:  # skip if you only want 'True' periods shaded
            continue

        fig.add_trace(
            go.Scatter(
                x=[row.x0, row.x0, row.x1, row.x1],
                y=[ymin, ymax, ymax, ymin],
                fill="toself",
                fillcolor="grey",
                opacity=0.25,
                line=dict(width=0),
                marker=dict(size=0, color="rgba(0,0,0,0.0)"),  # invisible markers in the rectangle corners
                showlegend=False,
                zorder=0,
                hoverinfo="skip",  # keeps the hover clean
                name="event span"  # optional – hidden because showlegend=False
            )
        )

    fig.update_layout(
        font=dict(size=18, color='black'),
        width=300,
        height=500,
        margin=dict(l=80, r=100, t=40, b=60),
    )

    col1, spacer = st.columns([1, 0.2])
    with col1:
        st.plotly_chart(fig, use_container_width=True)




