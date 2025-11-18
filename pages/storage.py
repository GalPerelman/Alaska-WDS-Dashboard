import pandas as pd
import numpy as np
import streamlit as st

import graph_utils
import utils


def storage_page():
    st.title("Storage Level")

    data = pd.read_csv("data/Arctic Village_water_level_data.csv", index_col=0)
    data["water_level_ft"] = data["water_level_m"] * 3.28084  # m to ft
    data["critical_threshold_ft"] = data["critical_threshold_m"] * 3.28084  # m to ft

    data["Date"] = data.index
    data["Date"] = pd.to_datetime(data["Date"])
    min_d, max_d = data["Date"].min().date(), data["Date"].max().date()
    date_win = st.slider(r"$\textsf{\Large Select window}$", min_value=min_d, max_value=max_d, value=(min_d, max_d))
    st.divider()
    mask = (data["Date"] >= pd.Timestamp(date_win[0])) & (data["Date"] <= pd.Timestamp(date_win[1]))
    filtered_data = data.loc[mask].copy()

    default_threshold = filtered_data["critical_threshold_ft"].iloc[0]
    threshold = st.number_input(label="Critical Water Level Threshold (ft):", min_value=0.0, value=default_threshold)

    fig = graph_utils.plot_time_series(
        data=filtered_data,
        data_col_names=["water_level_ft"],
        line_kw=dict(line_width=1.6))

    fig.add_hline(
        y=threshold,
        line=dict(color="red", dash="dash"),
        annotation_text=f"Critical ({threshold:.2f} ft)",
        annotation_position="top left",
        annotation_font_color="red",
    )

    # Identify contiguous True stretches
    # Every time the mask flips (True to False or False to True) we start a new group
    mask = filtered_data["water_level_ft"] < threshold
    filtered_data["group"] = (mask != mask.shift()).cumsum()

    df = filtered_data.loc[mask].reset_index(names="Timestamp")
    violation_ranges = (
        df
        .groupby("group")["Timestamp"]
        .agg(x0="min", x1="max")
    )

    for _, row in violation_ranges.iterrows():
        fig.add_shape(
            type="rect",
            x0=row.x0, x1=row.x1,
            xref="x",
            y0=0, y1=1,
            yref="paper",  # 0–1 = full vertical span
            fillcolor="white",  # translucent red
            line_width=0,
            opacity=0.2,
            layer="below"
        )

    fig.update_xaxes(
        title_text="Time",
        title_font_size=16,
        tickfont_size=14,
    )
    fig.update_yaxes(
        title_text="Water Level (ft)",
        title_font_size=16,
        tickfont_size=16,
    )

    fig.update_layout(
        hovermode="x unified"
    )

    fig.update_xaxes(tickfont=dict(size=utils.GRAPHS_FONT_SIZE))
    fig.update_yaxes(tickfont=dict(size=utils.GRAPHS_FONT_SIZE))
    fig.update_xaxes(title_font=dict(size=utils.GRAPHS_FONT_SIZE))
    fig.update_yaxes(title_font=dict(size=utils.GRAPHS_FONT_SIZE))
    st.plotly_chart(fig)

    def compute_metrics(df):
        df['time_only'] = df['Date'].dt.strftime('%H:%M:%S')
        mask_times = df['time_only'].isin([
            '00:15:00', '04:15:00', '08:15:00',
            '12:15:00', '16:15:00', '20:15:00'
        ])
        df_times = df[mask_times].copy()
        df_times.sort_values('Timestamp', inplace=True)
        df_times.reset_index(drop=True, inplace=True)

        df['threshold'] = threshold / 3.28084  # ft to m
        df["deficit_m"] = (df["threshold"] - df["water_level_m"]).clip(lower=0.0)
        D = df["deficit_m"]

        reliability = compute_reliability(D)
        resilience = compute_resilience(D)
        vulnerability = compute_vulnerability(D, target=threshold)
        return reliability, resilience, vulnerability

    rel1, res1, vul1 = compute_metrics(data)
    rel2, res2, vul2 = compute_metrics(filtered_data)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""<span style=' font-size: 20px; margin-top: 0;'>Complete Dataset Metrics</span>""",
                    unsafe_allow_html=True)
        all_data_col1, all_data_col2, all_data_col3, sp = st.columns(4)  # Organizes metrics horizontally
        with all_data_col1:
            st.metric("Reliability", f"{rel1:.3f}")
        with all_data_col2:
            st.metric("Resilience", f"{res1:.3f}")
        with all_data_col3:
            st.metric("Vulnerability", f"{vul1:.3f}")

    with (col2):
        st.markdown("""<span style=' font-size: 20px; margin-top: 0;'>Filtered Dataset Metrics</span>""",
                    unsafe_allow_html=True)
        filtered_data_col1, filtered_data_col2, filtered_data_col3, sp = st.columns(4)  # Organizes metrics horizontally
        with filtered_data_col1:
            delta = round((rel2 - rel1) / rel1, 3)
            delta = f"{delta:.2%}" if delta != 0.0 else None
            st.metric("Reliability", f"{rel2:.3f}", delta=delta)
        with filtered_data_col2:
            delta = round((res2 - res1) / res1, 3)
            delta = f"{delta:.2%}" if delta != 0.0 else None
            st.metric("Resilience", f"{res2:.3f}", delta=delta, delta_color="inverse")
        with filtered_data_col3:
            delta = round((vul2 - vul1) / vul1, 3)
            delta = f"{delta:.2%}" if delta != 0.0 else None
            st.metric("Vulnerability", f"{vul2:.3f}", delta=delta, delta_color="inverse")


def compute_reliability(deficits: pd.Series) -> float:
    """
    Time-based reliability (Eq. 2):
        Rel = (# of time steps with D_t = 0) / n
    where deficits D_t >= 0.
    """
    deficits = pd.Series(deficits).astype(float)
    n = len(deficits)
    if n == 0:
        return np.nan

    return (deficits == 0).sum() / n


def compute_resilience(deficits: pd.Series) -> float:
    """
    Resilience (Eq. 3):
        Res = (# of times D_t = 0 follows D_t > 0) / (# of times D_t > 0 occurred)
    i.e., probability that a success directly follows a failure.
    """
    deficits = pd.Series(deficits).astype(float)
    failures = deficits > 0

    n_fail = failures.sum()
    if n_fail == 0:
        # No failures -> resilience w.r.t. failures is undefined; often set to 1 or NaN by convention.
        return 0

    # A recovery is when we are successful now AND we were in failure at previous step.
    recoveries = (~failures & failures.shift(1, fill_value=False)).sum()

    return recoveries / n_fail


def compute_vulnerability(deficits: pd.Series, target: float) -> float:
    """
    Vulnerability (Eq. 4, 'dimensionless' version):
        Vul = (average deficit over failure periods) / target

    In Eq. (4) of the paper, 'Water demand_i' plays the role of a
    normalizing constant. Here we call it `target` (e.g., average threshold).
    """
    deficits = pd.Series(deficits).astype(float)
    failing_deficits = deficits[deficits > 0]

    if len(failing_deficits) == 0 or target == 0:
        return 0.0

    avg_deficit = failing_deficits.mean()
    return avg_deficit / target