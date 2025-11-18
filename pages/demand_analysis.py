import numpy as np
import pandas as pd
import calendar
import streamlit as st
import plotly.graph_objects as go

import graph_utils
import utils


def demand_analysis_page():
    st.markdown("""
        <style>
        .stHeadingContainer {
            margin-bottom: -20px;
        }
        </style>
        """, unsafe_allow_html=True)

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
        "Annually": "YS",
    }
    agg_map = {
        "Average": "mean",
        "Sum": "sum",
        "Maximum": "max",
        "Minimum": "min",
        "Median": "median",
    }

    col1, col2 = st.columns([1, 3])
    with col1:
        freq_label = st.selectbox("Resampling period", list(freq_map.keys()), index=1)
        freq = freq_map[freq_label]
    with col2:
        # agg_for_plot = st.selectbox("Aggregation for plot", list(agg_map.keys()), index=0)
        period_options = build_period_options(data.index, freq_label)
        selected_periods = st.multiselect("Select periods to present", period_options, key="selected_periods")

    def _select_all():
        st.session_state.selected_periods = period_options

    st.button("Select all", on_click=_select_all)

    #######################################################################################################
    # aggregated plot - keep for optional future use
    x_domain, x_kind = get_x_domain(freq_label)

    # aligned = {}
    # for p in selected_periods:
    #     if freq_label == "Daily":
    #         label = pd.Timestamp(p).strftime("%Y-%m-%d")
    #         aligned[label] = series_for_daily(data[DEMAND_COL].astype(float), p, how=agg_map[agg_for_plot])
    #     elif freq_label == "Weekly":
    #         start, end = p.split(" - ")
    #         label = f"{pd.Timestamp(start).date()} → {pd.Timestamp(end).date()}"
    #         aligned[label] = series_for_weekly(data[DEMAND_COL].astype(float), start, end, how=agg_map[agg_for_plot])
    #     elif freq_label == "Monthly":
    #         # p is "YYYY-MM"
    #         period = pd.Period(p, freq="M")
    #         ts = period.to_timestamp()
    #         label = ts.strftime("%b %Y")  # e.g. "Jan 2023"
    #         aligned[label] = series_for_monthly(
    #             data[DEMAND_COL].astype(float),
    #             year=ts.year,
    #             month=ts.month,
    #             how=agg_map[agg_for_plot],
    #         )
    #     elif freq_label == "Annually":
    #         year = int(p)
    #         label = str(year)
    #         aligned[label] = series_for_monthly_by_year(
    #             data[DEMAND_COL].astype(float),
    #             year=year,
    #             how=agg_map[agg_for_plot],
    #         )
    #######################################################################################################
    st.subheader("Hourly profiles", )
    aligned = {}
    hourly_fig = go.Figure()
    demand_series = data[DEMAND_COL].astype(float)
    if freq_label == "Daily":
        x_hours = list(range(24))
        for i, p in enumerate(selected_periods):
            label = pd.Timestamp(p).strftime("%Y-%m-%d")
            hourly_ser = series_for_daily(demand_series, p, how="mean")
            hourly_fig.add_trace(
                go.Scatter(
                    x=x_hours,
                    y=hourly_ser.values,
                    mode="lines",
                    line=dict(color=graph_utils.COLORS[i % len(graph_utils.COLORS)]),
                    name=label,
                )
            )
            aligned[label] = hourly_ser

    if freq_label == "Weekly":
        # Normalize each selected week to an "hour of week" axis: 0..167
        x_hours = list(range(24 * 7))
        for i, p in enumerate(selected_periods):
            start, end = p.split(" - ")
            hourly_ser = hourly_series_for_week(demand_series, start, end)
            hourly_fig.add_trace(
                go.Scatter(
                    x=x_hours[:len(hourly_ser)],
                    y=hourly_ser.values,
                    mode="lines",
                    line=dict(color=graph_utils.COLORS[i % len(graph_utils.COLORS)]),
                    name=p,
                    hovertemplate='(%{x:.1f}, %{y:.1f})<br>%{fullData.name}<extra></extra>'

                )
            )
            aligned[p] = hourly_ser

        hourly_fig.update_xaxes(title="Hour of week (0–167)")

    elif freq_label == "Monthly":
        # Normalize each selected month to an "hour of month" axis: 0..(31*24-1)
        x_hours = list(range(31 * 24))
        for i, p in enumerate(selected_periods):
            period = pd.Period(p, freq="M")
            ts = period.to_timestamp()
            label = ts.strftime("%b %Y")  # e.g. "Jan 2023"

            hourly_ser = hourly_series_for_month_aligned(demand_series, ts.year, ts.month)
            if hourly_ser.empty:
                continue

            hourly_fig.add_trace(
                go.Scatter(
                    x=x_hours[:len(hourly_ser)],
                    y=hourly_ser.values,
                    mode="lines",
                    line=dict(color=graph_utils.COLORS[i % len(graph_utils.COLORS)]),
                    name=label,
                    hovertemplate='(%{x:.1f}, %{y:.1f})<br>%{fullData.name}<extra></extra>'
                )
            )
            aligned[p] = hourly_ser

        hourly_fig.update_xaxes(title="Hour of month (0–744)")

    elif freq_label == "Annually":
        # Normalize each selected year to an "hour of year" axis: 0..(365*24-1)
        x_hours = list(range(365 * 24))
        for i, p in enumerate(selected_periods):
            year = int(p)
            label = str(year)
            hourly_ser = hourly_series_for_year_aligned(demand_series, year)
            if hourly_ser.empty:
                continue
            hourly_fig.add_trace(
                go.Scatter(
                    x=x_hours[:len(hourly_ser)],
                    y=hourly_ser.values,
                    mode="lines",
                    line=dict(color=graph_utils.COLORS[i % len(graph_utils.COLORS)]),
                    name=label,
                    hovertemplate='(%{x:.1f}, %{y:.1f})<br>%{fullData.name}<extra></extra>'
                )
            )
            aligned[p] = hourly_ser

        hourly_fig.update_xaxes(title="Hour of year (0–8759)")

    hourly_fig.update_layout(
        yaxis_title="Consumption (GPM)",
        yaxis=dict(tickformat=",.0f"),
    )
    hourly_fig.update_xaxes(tickfont=dict(size=utils.GRAPHS_FONT_SIZE))
    hourly_fig.update_yaxes(tickfont=dict(size=utils.GRAPHS_FONT_SIZE))
    hourly_fig.update_xaxes(title_font=dict(size=utils.GRAPHS_FONT_SIZE))
    hourly_fig.update_yaxes(title_font=dict(size=utils.GRAPHS_FONT_SIZE))
    hourly_fig.update_layout(margin=dict(t=5))
    st.plotly_chart(hourly_fig, use_container_width=True)
    #######################################################################################################
    # aggregated plot - keep for optional future use
    # st.text(" ")
    # st.subheader("Aggregated Data", )
    # fig = go.Figure()
    # for label, ser in aligned.items():
    #     fig.add_trace(go.Scatter(x=x_domain, y=ser.reindex(x_domain).values, mode="lines+markers", name=label))
    # fig.update_layout(
    #     yaxis_title="Consumption (GPM)",
    #     yaxis=dict(tickformat=",.0f")
    # )
    # fig.update_xaxes(tickfont=dict(size=utils.GRAPHS_FONT_SIZE))
    # fig.update_yaxes(tickfont=dict(size=utils.GRAPHS_FONT_SIZE))
    # fig.update_xaxes(title_font=dict(size=utils.GRAPHS_FONT_SIZE))
    # fig.update_yaxes(title_font=dict(size=utils.GRAPHS_FONT_SIZE))
    # fig.update_layout(margin=dict(t=0))
    # st.plotly_chart(fig, use_container_width=True)
    #######################################################################################################

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

    st.text(" ")
    st.subheader("Aggregated Statistics", )
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
    # Data was resampled above to hourly resolution
    # convert data to hourly units: from GPM to gallons per hour
    data[DEMAND_COL] = data[DEMAND_COL].astype(float) * 60.0
    # Now we sum hours per month-year thereby getting total gallons per month in Gallons units
    totals = data[DEMAND_COL].astype(float).groupby([data.index.month, data.index.year]).sum()
    totals = totals.reset_index()
    totals.columns = ["month", "year", "total"]

    pivot_df = totals.pivot(index="month", columns="year", values="total")
    fig = go.Figure()
    for i, year in enumerate(pivot_df.columns):
        months = pivot_df.index
        month_names = [calendar.month_name[m] for m in months]
        values = pivot_df[year].values
        color = graph_utils.BAR_COLORS[i]

        hover = (
            f"<span style='color:{color};'>"
            "%{customdata[0]} %{customdata[1]}: %{y:,.0f} GPM"
            "</span><extra></extra>"
        )

        fig.add_trace(
            go.Bar(
                x=[calendar.month_name[m] for m in pivot_df.index],  # month names
                y=pivot_df[year],
                name=str(year),
                customdata=np.stack([month_names, np.full(len(values), year)], axis=-1),
                hovertemplate=hover,
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
        yaxis_title="Monthly Consumption<br>(Gallons)",
        yaxis=dict(tickformat=",.0f")
    )
    fig.update_xaxes(tickfont=dict(size=utils.GRAPHS_FONT_SIZE))
    fig.update_yaxes(tickfont=dict(size=utils.GRAPHS_FONT_SIZE))
    fig.update_xaxes(title_font=dict(size=utils.GRAPHS_FONT_SIZE))
    fig.update_yaxes(title_font=dict(size=utils.GRAPHS_FONT_SIZE))
    fig.update_layout(margin=dict(t=0))
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
        # unique month-year periods present in the data
        months = idx.to_period("M").unique()
        # store as YYYY-MM; we can pretty-print later as "Jan 2023"
        options = [m.strftime("%Y-%m") for m in months]
        return options

    if mode == "Annually":
        years = pd.Index(idx.year.unique()).sort_values()
        options = [f"{int(y)}" for y in years]
        return options

    return []


def get_x_domain(mode: str):
    if mode == "Daily":
        # hours 0..23
        return list(range(24)), "hour"
    if mode == "Weekly":
        # Monday - Sunday mapped to 0..6
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        return days, "dow"  # day-of-week label
    if mode == "Monthly":
        return list(range(1, 32)), "dom"
    if mode == "Annually":
        # Months of the year Jan - Dec
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


def series_for_monthly(s: pd.Series, year: int, month: int, how="sum"):
    """
    Aggregate a given month-year into a day-of-month profile.

    Returns a Series indexed by day-of-month 1..31.
    """
    mask = (s.index.year == year) & (s.index.month == month)
    ss = s.loc[mask]
    days = range(1, 32)
    if ss.empty:
        return pd.Series(index=days, dtype=float)

    grouped = ss.groupby(ss.index.day)
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
    else:
        raise ValueError(f"Unknown aggregation: {how}")

    # ensure we always have 1..31 for consistent x_domain
    return out.reindex(days, fill_value=np.nan)


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


def hourly_series_for_week(s: pd.Series, start_date, end_date) -> pd.Series:
    """
    Return a 1D hourly series for a given [start_date, end_date] week,
    aligned to a 0..167 'hour of week' index.
    """
    start = pd.Timestamp(start_date)
    # include the full last day up to 23:00
    end = pd.Timestamp(end_date) + pd.Timedelta(days=1) - pd.Timedelta(hours=1)

    ss = s.loc[(s.index >= start) & (s.index <= end)]
    if ss.empty:
        return pd.Series(index=pd.RangeIndex(24 * 7), dtype=float)

    # ensure hourly frequency
    ss = ss.resample("h").mean()

    expected_len = 24 * 7
    ss = ss.iloc[:expected_len]  # just in case there is extra data
    # normalize index to 0..len-1 so we can align weeks on top of each other
    ss.index = pd.RangeIndex(len(ss))

    # pad if we have fewer than 168 points
    if len(ss) < expected_len:
        ss = ss.reindex(pd.RangeIndex(expected_len))

    return ss


def hourly_series_for_month(s: pd.Series, year: int, month: int) -> pd.Series:
    ss = s[(s.index.year == year) & (s.index.month == month)]
    if ss.empty:
        return pd.Series(dtype=float)
    return ss.resample("h").mean()


def hourly_series_for_year(s: pd.Series, year: int) -> pd.Series:
    """
    Return an hourly series for a given year, indexed by the actual timestamps.
    """
    ss = s.loc[s.index.year == int(year)]
    if ss.empty:
        return pd.Series(dtype=float)

    ss = ss.resample("h").mean()
    return ss


def hourly_series_for_month_aligned(s: pd.Series, year: int, month: int) -> pd.Series:
    """
    Return a 1D hourly series for a given month-year,
    aligned to a 0..(31*24-1) 'hour of month' index.
    """
    start = pd.Timestamp(year=year, month=month, day=1)

    # first day of the next month
    if month == 12:
        next_month = pd.Timestamp(year=year + 1, month=1, day=1)
    else:
        next_month = pd.Timestamp(year=year, month=month + 1, day=1)

    # include full last day up to 23:00
    end = next_month - pd.Timedelta(hours=1)

    ss = s.loc[(s.index >= start) & (s.index <= end)]
    if ss.empty:
        return pd.Series(index=pd.RangeIndex(31 * 24), dtype=float)

    ss = ss.resample("h").mean().sort_index()

    expected_len = 31 * 24
    ss = ss.iloc[:expected_len]          # just in case
    ss.index = pd.RangeIndex(len(ss))    # 0..len-1

    if len(ss) < expected_len:
        ss = ss.reindex(pd.RangeIndex(expected_len))

    return ss


def hourly_series_for_year_aligned(s: pd.Series, year: int) -> pd.Series:
    """
    Return a 1D hourly series for a given year,
    aligned to a 0..(365*24-1) 'hour of year' index.

    For leap years, the extra day is truncated.
    """
    start = pd.Timestamp(year=year, month=1, day=1)
    end = pd.Timestamp(year=year + 1, month=1, day=1) - pd.Timedelta(hours=1)

    ss = s.loc[(s.index >= start) & (s.index <= end)]
    if ss.empty:
        return pd.Series(index=pd.RangeIndex(365 * 24), dtype=float)

    ss = ss.resample("h").mean().sort_index()

    expected_len = 365 * 24
    ss = ss.iloc[:expected_len]        # truncate if leap year or extra data
    ss.index = pd.RangeIndex(len(ss))  # 0..len-1

    if len(ss) < expected_len:
        ss = ss.reindex(pd.RangeIndex(expected_len))

    return ss