import numpy as np
import pandas as pd
import calendar
import streamlit as st
import plotly.graph_objects as go

import graph_utils


def demand_analysis_page():
    st.title("Demand Analysis")
    DEMAND_COL = "Master Meter Flow Rate, GPM"

    data = pd.read_csv("data/raw_timeseries_data.csv", index_col=0)
    data = pd.read_csv("data/1_raw sensor data/3_system_flow.csv", index_col=0)
    data.index = pd.to_datetime(data.index)
    data = data.resample("60min").mean()  # ensure regular 1-h intervals

    freq_map = {
        "Daily": "D",
        "Weekly": "W",
        "Monthly": "MS",
    }
    agg_map = {
        "Average": "mean",
        "Sum": "sum",
        "Maximum": "max",
        "Minimum": "min",
        "Median": "median",
    }

    col1, col2 = st.columns([1, 1])
    with col1:
        freq_label = st.selectbox("Resampling period", list(freq_map.keys()), index=1)
        freq = freq_map[freq_label]
    with col2:
        agg_for_plot = st.selectbox("Aggregation for plot", list(agg_map.keys()), index=0)

    period_options = build_period_options(data.index, freq_label)
    selected_periods = st.multiselect("Select periods to present", period_options, key="selected_periods")

    def _select_all():
        st.session_state.selected_periods = period_options

    st.button("Select all", on_click=_select_all)

    x_domain, x_kind = get_x_domain(freq_label)

    aligned = {}
    for p in selected_periods:
        if freq_label == "Daily":
            label = pd.Timestamp(p).strftime("%Y-%m-%d")
            aligned[label] = series_for_daily(data[DEMAND_COL].astype(float), p, how=agg_map[agg_for_plot])
        elif freq_label == "Weekly":
            start, end = p.split(" - ")
            label = f"{pd.Timestamp(start).date()} → {pd.Timestamp(end).date()}"
            aligned[label] = series_for_weekly(data[DEMAND_COL].astype(float), start, end, how=agg_map[agg_for_plot])
        elif freq_label == "Monthly":
            label = str(int(p))
            aligned[label] = series_for_monthly_by_year(data[DEMAND_COL].astype(float), int(p), how=agg_map[agg_for_plot])

    fig = go.Figure()
    for label, ser in aligned.items():
        fig.add_trace(go.Scatter(x=x_domain, y=ser.reindex(x_domain).values, mode="lines+markers", name=label))
    fig.update_layout(
        yaxis_title="Consumption (GPM)",
        yaxis=dict(tickformat=",.0f")
    )
    st.plotly_chart(fig, use_container_width=True)

    # Add Statistics table
    def summarize_period(ser: pd.Series) -> pd.Series:
        s = ser.dropna()
        return pd.Series({
            "Average": s.mean(),
            "Min": s.min(),
            "Max": s.max(),
            "Total": s.sum(),
        })
    # Rows = selected periods (labels), Columns = stats
    stats_df = pd.DataFrame({label: summarize_period(ser) for label, ser in aligned.items()}).T

    # Optional: nice formatting
    fmt = {c: "{:,.2f}" for c in stats_df.columns}

    st.subheader("Statistics", )
    csv = stats_df.to_csv(index=True).encode("utf-8")
    st.download_button(
        label="Download Table",
        data=csv,
        file_name="statistics.csv",
        mime="text/csv",
    )

    def stats_table_plotly(df, col_width=120):
        # Build header + cells
        header_vals = ([df.index.name or "Period"] + list(df.columns))
        cells_vals = [df.index.astype(str).tolist()] + [df[c].tolist() for c in df.columns]

        fig = go.Figure(data=[go.Table(
            columnwidth=[col_width] * len(header_vals),
            header=dict(values=header_vals,
                        align="center",
                        font=dict(size=16, weight='bold'),
                        height=36),
            cells=dict(values=cells_vals,
                       align="center",
                       height=36,
                       format=[None] + [",.2f"] * len(df.columns),
                       font=dict(size=14))
        )])
        # Auto height: ~row_count * row_height + header
        fig.update_layout(margin=dict(l=0, r=0, t=0, b=0),
                          height=min(250, int((len(df) + 1) * 32 + 40))
                          )
        st.plotly_chart(fig, use_container_width=True)

    stats_table_plotly(stats_df)

    st.subheader("Monthly Totals", )
    totals = data[DEMAND_COL].astype(float).groupby([data.index.month, data.index.year]).sum()
    totals = totals.reset_index()
    totals.columns = ["month", "year", "total"]

    pivot_df = totals.pivot(index="month", columns="year", values="total")
    fig = go.Figure()
    for i, year in enumerate(pivot_df.columns):
        fig.add_trace(
            go.Bar(
                x=[calendar.month_name[m] for m in pivot_df.index],  # month names
                y=pivot_df[year],
                name=str(year),
                marker=dict(
                    color=graph_utils.BAR_COLORS[i],
                    line=dict(
                        color="black",  # edge color
                        width=1  # edge thickness
                    )
                )
            )
        )

    # Update layout
    fig.update_layout(
        barmode="group",  # side-by-side grouped bars
        yaxis_title="Total Consumption (GPM)",
        yaxis=dict(tickformat=",.0f")
    )
    st.plotly_chart(fig, use_container_width=True)


def build_period_options(idx: pd.DatetimeIndex, mode: str):
    idx = idx.sort_values()
    if mode == "Daily":
        # unique calendar dates present in data
        dates = pd.to_datetime(idx.date).unique()
        # return label and value both as date for simplicity
        options = [(d.strftime("%Y-%m-%d")) for d in dates]
        return options

    if mode == "Weekly":
        # ISO weeks aligned to Monday. For each week, show [start..end]
        weeks = idx.to_series().dt.to_period("W-MON").unique()
        options = []
        for w in weeks:
            start = w.start_time.normalize()
            end = w.end_time.normalize()
            label = f"{start.date()} - {end.date()}"
            options.append((label))
        return options

    if mode == "Monthly":
        # Compare months within a YEAR → user picks one or more YEARS
        years = pd.Index(idx.year.unique()).sort_values()
        options = [f"{int(y)}" for y in years]
        return options

    return []


def get_x_domain(mode: str):
    if mode == "Daily":
        # hours 0..23
        return list(range(24)), "hour"
    if mode == "Weekly":
        # Monday..Sunday mapped to 0..6
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        return days, "dow"  # day-of-week label
    if mode == "Monthly":
        # Months of the year Jan..Dec
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        return months, "month"
    return [], ""


def series_for_daily(s: pd.Series, the_date, how):
    mask = s.index.date == pd.Timestamp(the_date).date()
    ss = s.loc[mask]
    if ss.empty:
        return pd.Series(index=range(24), dtype=float)
    grouped = ss.groupby(ss.index.hour)
    if how == "sum":
        out = grouped.sum()
    elif how == "mean":
        out = grouped.mean()
    elif how == "max":
        out = grouped.max()
    elif how == "min":
        out = grouped.min()
    elif how == "median":
        out = grouped.median()
    return out.reindex(range(24), fill_value=np.nan)


def series_for_weekly(s: pd.Series, start_date, end_date, how="sum"):
    start = pd.Timestamp(start_date)
    end = pd.Timestamp(end_date) + pd.Timedelta(days=1) - pd.Timedelta(microseconds=1)
    ss = s.loc[(s.index >= start) & (s.index <= end)]
    if ss.empty:
        return pd.Series(index=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"], dtype=float)
    # map to Mon..Sun
    dow_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    grouped = ss.groupby(ss.index.dayofweek)
    if how == "sum":
        out = grouped.sum()
    elif how == "mean":
        out = grouped.mean()
    elif how == "max":
        out = grouped.max()
    elif how == "min":
        out = grouped.min()
    elif how == "median":
        out = grouped.median()
    out.index = [dow_names[i] for i in out.index]
    return out.reindex(dow_names, fill_value=np.nan)


def series_for_monthly_by_year(s: pd.Series, year: int, how="sum"):
    ss = s.loc[(s.index.year == int(year))]
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    if ss.empty:
        return pd.Series(index=months, dtype=float)
    grouped = ss.groupby(ss.index.month)
    if how == "sum":
        out = grouped.sum()
    elif how == "mean":
        out = grouped.mean()
    elif how == "max":
        out = grouped.max()
    elif how == "min":
        out = grouped.min()
    elif how == "median":
        out = grouped.median()
    # map 1..12 -> month names
    out.index = [months[m - 1] for m in out.index]
    return out.reindex(months, fill_value=np.nan)
