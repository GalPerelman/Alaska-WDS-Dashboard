import streamlit as st
import base64

GRAPHS_FONT_SIZE = 24


def custom_button(png_path: str, label: str, button_id: str):
    with open(png_path, "rb") as f:
        data = f.read()
    encoded = base64.b64encode(data).decode()

    # CSS + HTML template
    button_html = f"""
        <style>
        .custom-button-{button_id} {{
            
            display: flex;
            flex-direction: column;   /* stack vertically */
            align-items: center;      /* center horizontally */
            justify-content: center;  /* center vertically */
            background-color: black;
            color: white;
            padding: 12px 20px;
            border: white 2px solid;
            border-radius: 8px;
            text-decoration: none;
            font-size: 20px;
            cursor: pointer;
            text-align: center;

        }}
        .custom-button-{button_id} img {{
            height: 100px;
        }}
        </style>
        <a class="custom-button-{button_id}" target="_self" href="?clicked={button_id}">
            <img src="data:image/png;base64,{encoded}">
            {label}
        </a>
    """
    st.markdown(button_html, unsafe_allow_html=True)


def resize_to_height(img, target_h):
    w, h = img.size
    new_w = int(w * target_h / h)
    return img.resize((new_w, target_h))