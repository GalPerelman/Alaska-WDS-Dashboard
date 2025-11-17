import streamlit as st


def main_page():
    st.title("About")

    st.text("This dashboard uses water system key component sensor data to establish demand patterns, derive pump curves, determine unmeasured water losses, and assess sustainability metrics. It is set-up to facilitate decision making by allowing operators to assess different operation scenarios. ")

    st.markdown("Paper (to update later) [link](%s)" %"https://sites.utexas.edu/selalina/")
    st.text(" ")

    col1, col2 = st.columns(2)
    with col1:
        st.image("resources/unalakleet1.jpg", caption="")
    with col2:
        st.image("resources/unalakleet2.jpg", caption="")