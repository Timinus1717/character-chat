import os
import json
import time
import base64
from datetime import datetime, timezone, timedelta
import streamlit as st
from openai import OpenAI

# 1. Page Configuration
st.set_page_config(
    page_title="Story Chat",
    page_icon="💬",
    layout="centered",
    initial_sidebar_state="expanded"
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 2. Hong Kong Time Helper (UTC+8)
def get_hkt_time():
    hkt_zone = timezone(timedelta(hours=8))
    return datetime.now(hkt_zone).strftime("%I:%M %p").lower()

# 3. Base64 Image Encoder
def get_image_base64(relative_path):
    if not relative_path:
        return None
    full_path = os.path.join(BASE_DIR, relative_path)
    if os.path.isfile(full_path):
        with open(full_path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode()
            ext = os.path.splitext(full_path)[1].lower().replace(".", "")
            mime = "jpeg" if ext in ["jpg", "jpeg"] else ext
            return f"data:image/{mime};base64,{encoded}"
    return None

# 4. High-Contrast Sky-Blue & Pure White CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
    }

    header[data-testid="stHeader"] {
        background: transparent !important;
        pointer-events: none !important;
    }
    header[data-testid="stHeader"] button, 
    header[data-testid="stHeader"] a {
        pointer-events: auto !important;
    }

    .stApp {
        background-color: #e6f4fd !important;
    }

    .block-container {
        padding-top: 0.5rem !important;
        padding-bottom: 140px !important;
        max-width: 660px !important;
        background-color: transparent !important;
    }

    div[data-testid="stElementContainer"]:has(.chat-top-header),
    .element-container:has(.chat-top-header),
    div:has(> div > .chat-top-header) {
        position: sticky !important;
        top: 0 !important;
        z-index: 9999 !important;
        background-color: #e6f4fd !important;
        padding-top: 10px !important;
        padding-bottom: 12px !important;
        margin-top: -10px !important;
    }

    .chat-top-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        background: #ffffff !important;
        padding: 14px 22px;
        border-radius: 26px;
        box-shadow: 0 6px 20px rgba(2, 132, 199, 0.12);
        position: relative;
        z-index: 10000;
        border: 2px solid #ffffff;
    }
    .header-left {
        display: flex;
        align-items: center;
        gap: 12px;
    }
    .back-arrow-btn {
        font-size: 1.15rem;
        color: #475569 !important;
        font-weight: 700;
    }
    .header-titles h3 {
        margin: 0;
        font-size: 1.25rem;
        font-weight: 700;
        color: #0f172a !important;
        letter-spacing: -0.01em;
    }

    .online-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        margin: 0;
        font-size: 0.84rem;
        font-weight: 700;
        color: #047857 !important;
    }
    .status-dot-glow {
        width: 9px;
        height: 9px;
        background-color: #10b981;
        border-radius: 50%;
        display: inline-block;
        box-shadow: 0 0 6px #10b981, 0 0 12px rgba(16, 185, 129, 0.6);
        animation: pulseGlow 2s infinite ease-in-out;
    }
    @keyframes pulseGlow {
        0%, 100% {
            transform: scale(0.95);
            box-shadow: 0 0 4px #10b981, 0 0 8px rgba(16, 185, 129, 0.5);
        }
        50% {
            transform: scale(1.15);
            box-shadow: 0 0 8px #10b981, 0 0 16px rgba(16, 185, 129, 0.9);
        }
    }

    .header-avatar {
        width: 52px;
        height: 52px;
        border-radius: 50%;
        object-fit: cover;
        box-shadow: 0 4px 12px rgba(2, 132, 199, 0.25);
        border: 2.5px solid #0284c7;
    }
    .header-avatar-fallback {
        width: 52px;
        height: 52px;
        border-radius: 50%;
        background: #0284c7;
        color: white;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 24px;
    }

    .msg-row {
        display: flex;
        width: 100%;
        margin-bottom: 14px;
        position: relative;
        z-index: 1;
    }
    .msg-row.user {
        justify-content: flex-end;
    }
    .msg-row.assistant {
        justify-content: flex-start;
    }

    .msg-bubble {
        position: relative;
        max-width: 82%;
        padding: 13px 18px;
        font-size: 0.97rem;
        line-height: 1.55;
        word-wrap: break-word;
        white-space: pre-wrap;
    }

    .msg-bubble.user {
        background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%) !important;
        color: #ffffff !important;
        font-weight: 500;
        border-radius: 22px 22px 4px 22px;
        box-shadow: 0 4px 14px rgba(2, 132, 199, 0.25);
    }

    .msg-bubble.assistant {
        background: #ffffff !important;
        color: #0f172a !important;
        font-weight: 500;
        border-radius: 22px 22px 22px 4px;
        box-shadow: 0 4px 14px rgba(15, 23, 42, 0.08);
        border: 1.5px solid #cbd5e1 !important;
    }

    .typing-pill {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: #ffffff !important;
        padding: 8px 16px;
        border-radius: 20px;
        margin-bottom: 12px;
        color: #0369a1 !important;
        font-size: 0.85rem;
        font-weight: 700;
        border: 1px solid #bae6fd;
        box-shadow: 0 2px 8px rgba(2, 132, 199, 0.10);
    }

    .block-container .stButton button {
        background-color: #ffffff !important;
        color: #0369a1 !important;
        border: 1.5px solid #93c5fd !important;
        border-radius: 20px !important;
        font-size: 0.86rem !important;
        font-weight: 700 !important;
        padding: 8px 14px !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 2px 6px rgba(2, 132, 199, 0.08) !important;
    }
    .block-container .stButton button:hover {
        background: #0284c7 !important;
        color: #ffffff !important;
        border-color: #0284c7 !important;
        transform: translateY(-1px);
        box-shadow: 0 6px 14px rgba(2, 132, 199, 0.3) !important;
    }

    [data-testid="stBottom"],
    [data-testid="stBottom"] > div,
    [data-testid="stBottom"] > div > div {
        background: transparent !important;
        background-color: transparent !important;
        border: none !important;
    }

    [data-testid="stChatInput"] {
        background-color: #ffffff !important;
        border-radius: 36px !important;
        border: 2px solid #93c5fd !important;
        box-shadow: 0 10px 25px -4px rgba(2, 132, 199, 0.25), 0 4px 12px rgba(0, 0, 0, 0.06) !important;
        padding: 6px 10px 6px 18px !important;
        margin-bottom: 12px !important;
    }

    [data-testid="stChatInput"] > div,
    [data-testid="stChatInput"] textarea {
        background-color: #ffffff !important;
        color: #0f172a !important;
        font-size: 0.96rem !important;
        caret-color: #0284c7 !important;
        font-weight: 500 !important;
    }
    [data-testid="stChatInput"] textarea::placeholder {
        color: #64748b !important;
        font-weight: 500 !important;
    }

    [data-testid="stChatInput"] button {
        background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%) !important;
        color: #ffffff !important;
        border-radius: 50% !important;
        width: 38px !important;
        height: 38px !important;
        border: none !important;
        box-shadow: 0 4px 12px rgba(2, 132, 199, 0.35) !important;
    }
    [data-testid="stChatInput"] button svg {
        fill: #ffffff !important;
    }

    /* =========================================================
       SIDEBAR & STABLE COLUMN RENDERING
       ========================================================= */
    [data-testid="stSidebar"] {
        background-color: #ffffff !important;
        border-right: 1.5px solid #cbd5e1 !important;
    }
    [data-testid="stSidebar"] > div:first-child {
        display: flex;
        flex-direction: column;
        height: 100vh;
        overflow-y: auto;
        padding-bottom: 0 !important;
        background-color: #ffffff !important;
    }
    [data-testid="stSidebar"] h1, 
    [data-testid="stSidebar"] h2, 
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] p {
        color: #0f172a !important;
        font-weight: 700;
        margin-bottom: 0.25rem !important;
    }

    [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
        gap: 0.25rem !important;
    }
    [data-testid="stSidebar"] [data-testid="stElementContainer"] {
        margin-bottom: 0 !important;
        padding-bottom: 0 !important;
    }

    /* Prevent vertical overlap in the column containers */
    [data-testid="stSidebar"] [data-testid="stHorizontalBlock"] {
        align-items: center !important;
        margin-top: 2px !important;
        margin-bottom: 2px !important;
        gap: 0.4rem !important;
    }

    /* Book Bubbles */
    .book-bubble-thumb {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        object-fit: cover;
        border: 2px solid #0284c7;
        box-shadow: 0 2px 6px rgba(2, 132, 199, 0.15);
        display: block;
        margin: auto;
    }
    .book-bubble-fallback {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        background: #0284c7;
        color: white;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 19px;
        box-shadow: 0 2px 6px rgba(2, 132, 199, 0.15);
        margin: auto;
    }

    .sidebar-book-btn .stButton button {
        background-color: #f0f9ff !important;
        color: #0c4a6e !important;
        border: 1.5px solid #bae6fd !important;
        border-radius: 12px !important;
        font-size: 0.88rem !important;
        font-weight: 700 !important;
        padding: 6px 10px !important;
        text-align: left !important;
        justify-content: flex-start !important;
        white-space: normal !important;
        word-break: break-word !important;
        line-height: 1.25 !important;
        width: 100% !important;
        box-shadow: 0 1px 3px rgba(2, 132, 199, 0.06) !important;
        transition: all 0.2s ease !important;
        min-height: 38px !important;
        margin: 0 !important;
    }
    .sidebar-book-btn .stButton button:hover {
        background-color: #e0f2fe !important;
        border-color: #0284c7 !important;
        color: #0284c7 !important;
    }

    /* Character Bubbles */
    .char-bubble-thumb {
        width: 32px;
        height: 32px;
        border-radius: 50%;
        object-fit: cover;
        border: 1.5px solid #93c5fd;
        display: block;
        margin: auto;
    }
    .char-bubble-thumb-active {
        width: 32px;
        height: 32px;
        border-radius: 50%;
        object-fit: cover;
        border: 2px solid #0284c7;
        box-shadow: 0 0 8px rgba(2, 132, 199, 0.45);
        display: block;
        margin: auto;
    }
    .char-bubble-fallback {
        width: 32px;
        height: 32px;
        border-radius: 50%;
        background: #e0f2fe;
        color: #0284c7;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 14px;
        margin: auto;
    }

    .sidebar-char-btn .stButton button {
        background-color: #ffffff !important;
        color: #1e293b !important;
        border: 1.5px solid #cbd5e1 !important;
        border-radius: 10px !important;
        font-size: 0.83rem !important;
        font-weight: 600 !important;
        padding: 5px 8px !important;
        text-align: left !important;
        justify-content: flex-start !important;
        white-space: normal !important;
        word-break: break-word !important;
        line-height: 1.2 !important;
        width: 100% !important;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04) !important;
        transition: all 0.2s ease !important;
        min-height: 32px !important;
        margin: 0 !important;
    }
    .sidebar-char-btn .stButton button:hover {
        background-color: #e0f2fe !important;
        color: #0284c7 !important;
        border-color: #0284c7 !important;
    }
    .sidebar-char-btn-active .stButton button {
        background-color: #0284c7 !important;
        color: #ffffff !important;
        border: 1.5px solid #0284c7 !important;
        border-radius: 10px !important;
        font-size: 0.83rem !important;
        font-weight: 700 !important;
        padding: 5px 8px !important;
        text-align: left !important;
        justify-content: flex-start !important;
        white-space: normal !important;
        word-break: break-word !important;
        line-height: 1.2 !important;
        width: 100% !important;
        box-shadow: 0 2px 8px rgba(2, 132, 199, 0.3) !important;
        min-height: 32px !important;
        margin: 0 !important;
    }

    /* Sticky Profile Card at Bottom of Sidebar */
    div[data-testid="stElementContainer"]:has(.locked-profile-anchor),
    .element-container:has(.locked-profile-anchor) {
        position: sticky !important;
        bottom: 0 !important;
        z-index: 1000 !important;
        background: #ffffff !important;
        padding-top: 8px !important;
        padding-bottom: 8px !important;
        margin-top: auto !important;
        box-shadow: 0 -12px 24
