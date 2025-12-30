# config.py
import os

try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False


def get_secret(key: str) -> str:
    if STREAMLIT_AVAILABLE and key in st.secrets:
        return st.secrets[key]

    value = os.getenv(key)
    if not value:
        raise RuntimeError(f"Missing required secret: {key}")

    return value
