from pathlib import Path
import base64

import streamlit as st


def _load_image_base64(path: Path) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def inject_custom_header(logo_path: Path, title: str) -> None:
    if not logo_path.exists():
        st.warning(f"Logo not found at {logo_path}")
        return

    logo_b64 = _load_image_base64(logo_path)
    st.markdown(
        f"""
        <style>
        [data-testid="stHeader"] {{
            display: none;
        }}

        .custom-header {{
            background-color: #111827;
            display: flex;
            align-items: center;
            gap: 16px;
            height: 70px;
            padding: 0 24px;
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            width: 100%;
            z-index: 9999;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}

        .custom-header img {{
            height: 40px;
        }}

        .custom-header-title {{
            color: #FFFFFF;
            font-size: 22px;
            font-weight: 600;
            margin: 0;
            font-family: Arial, sans-serif;
        }}

        .main .block-container {{
            padding-top: 90px;
        }}
        </style>

        <div class="custom-header">
            <img src="data:image/png;base64,{logo_b64}" alt="logo">
            <div class="custom-header-title">{title}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
