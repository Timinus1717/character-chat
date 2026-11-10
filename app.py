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

# 4. High-Contrast Sky-Blue & Pure White CSS (Tight Sidebar Spacing)
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
       SIDEBAR: TIGHTENED VERTICAL NAVIGATION SPACING
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

    /* Tighten default Streamlit vertical block gaps */
    [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
        gap: 0.25rem !important;
    }
    [data-testid="stSidebar"] [data-testid="stElementContainer"] {
        margin-bottom: 0 !important;
        padding-bottom: 0 !important;
    }

    /* Vertically align image columns with button columns & minimize vertical margins */
    [data-testid="stSidebar"] [data-testid="stHorizontalBlock"] {
        align-items: center !important;
        margin-top: 1px !important;
        margin-bottom: 2px !important;
        gap: 0.35rem !important;
    }

    /* Book Bubbles */
    .book-bubble-thumb {
        width: 44px;
        height: 44px;
        border-radius: 50%;
        object-fit: cover;
        border: 2.5px solid #0284c7;
        box-shadow: 0 2px 6px rgba(2, 132, 199, 0.15);
        display: block;
        margin: auto;
    }
    .book-bubble-fallback {
        width: 44px;
        height: 44px;
        border-radius: 50%;
        background: #0284c7;
        color: white;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 20px;
        box-shadow: 0 2px 6px rgba(2, 132, 199, 0.15);
        margin: auto;
    }

    /* Book Title Buttons - Compact vertical padding */
    .sidebar-book-btn {
        margin-top: 3px !important;
    }
    .sidebar-book-btn .stButton button {
        background-color: #f0f9ff !important;
        color: #0c4a6e !important;
        border: 1.5px solid #bae6fd !important;
        border-radius: 12px !important;
        font-size: 0.88rem !important;
        font-weight: 700 !important;
        padding: 5px 10px !important;
        text-align: left !important;
        justify-content: flex-start !important;
        white-space: normal !important;
        word-break: break-word !important;
        line-height: 1.25 !important;
        width: 100% !important;
        box-shadow: 0 1px 3px rgba(2, 132, 199, 0.06) !important;
        transition: all 0.2s ease !important;
        min-height: 40px !important;
        margin: 0 !important;
    }
    .sidebar-book-btn .stButton button:hover {
        background-color: #e0f2fe !important;
        border-color: #0284c7 !important;
        color: #0284c7 !important;
    }

    /* Indented Character Bubbles */
    .char-bubble-thumb {
        width: 34px;
        height: 34px;
        border-radius: 50%;
        object-fit: cover;
        border: 1.5px solid #93c5fd;
        display: block;
        margin: auto;
    }
    .char-bubble-thumb-active {
        width: 34px;
        height: 34px;
        border-radius: 50%;
        object-fit: cover;
        border: 2px solid #0284c7;
        box-shadow: 0 0 8px rgba(2, 132, 199, 0.45);
        display: block;
        margin: auto;
    }
    .char-bubble-fallback {
        width: 34px;
        height: 34px;
        border-radius: 50%;
        background: #e0f2fe;
        color: #0284c7;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 15px;
        margin: auto;
    }

    /* Character Selection Buttons - Compact vertical padding */
    .sidebar-char-btn .stButton button {
        background-color: #ffffff !important;
        color: #1e293b !important;
        border: 1.5px solid #cbd5e1 !important;
        border-radius: 10px !important;
        font-size: 0.83rem !important;
        font-weight: 600 !important;
        padding: 4px 8px !important;
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
        padding: 4px 8px !important;
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
        box-shadow: 0 -12px 24px -4px rgba(2, 132, 199, 0.12) !important;
        border-top: 1.5px solid #cbd5e1 !important;
    }

    .light-profile-card {
        background: #f8fafc !important;
        border-radius: 18px;
        padding: 10px 10px;
        text-align: center;
        border: 1.5px solid #cbd5e1 !important;
    }
    .light-profile-avatar {
        width: 60px;
        height: 60px;
        border-radius: 50%;
        object-fit: cover;
        margin: 0 auto 4px auto;
        display: block;
        border: 2.5px solid #0284c7;
        box-shadow: 0 4px 12px rgba(2, 132, 199, 0.25);
    }
    .light-profile-avatar-fallback {
        width: 60px;
        height: 60px;
        border-radius: 50%;
        background: #0284c7;
        color: white;
        font-size: 28px;
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 0 auto 4px auto;
    }
    .light-profile-name {
        font-size: 0.96rem;
        font-weight: 700;
        color: #0f172a !important;
        margin-bottom: 1px;
    }
    .light-profile-book {
        font-size: 0.76rem;
        color: #0369a1 !important;
        font-weight: 700;
        margin-bottom: 4px;
    }
    .light-profile-bio {
        background: #ffffff !important;
        border: 1px solid #cbd5e1;
        border-radius: 10px;
        padding: 6px 8px;
        font-size: 0.78rem;
        color: #1e293b !important;
        text-align: left;
        line-height: 1.4;
        font-weight: 500;
    }

    .clear-chat-container .stButton button {
        background-color: #ffffff !important;
        color: #be123c !important;
        border: 1.5px solid #fda4af !important;
        border-radius: 16px !important;
        font-size: 0.80rem !important;
        font-weight: 700 !important;
        padding: 5px 10px !important;
        margin-top: 4px !important;
        transition: all 0.2s ease !important;
    }
    .clear-chat-container .stButton button:hover {
        background-color: #ffe4e6 !important;
        border-color: #f43f5e !important;
        color: #9f1239 !important;
    }
</style>
""", unsafe_allow_html=True)

# 5. OpenRouter Connection
api_key = st.secrets.get("OPENROUTER_API_KEY", "")
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key or "missing_key"
)

# Unrestricted paid tier model
MODEL_NAME = "meta-llama/llama-3.3-70b-instruct"

# 6. Load Catalog
def load_catalog():
    with open(os.path.join(BASE_DIR, "characters.json"), "r", encoding="utf-8") as f:
        data = json.load(f)
    standardized = {}
    for story_title, story_val in data.items():
        if isinstance(story_val, list):
            standardized[story_title] = {"cover": "", "characters": story_val}
        else:
            standardized[story_title] = story_val
    return standardized

catalog = load_catalog()
all_stories = list(catalog.keys())

# 7. Persistent Session Initialization
if "character_chats" not in st.session_state:
    st.session_state.character_chats = {}

if "failed_prompts" not in st.session_state:
    st.session_state.failed_prompts = {}

if "selected_story" not in st.session_state:
    st.session_state.selected_story = all_stories[0]

first_char_name = catalog[st.session_state.selected_story]["characters"][0]["name"]
if "selected_char" not in st.session_state:
    st.session_state.selected_char = first_char_name

# Track open dropdowns (default first story expanded)
if "expanded_stories" not in st.session_state:
    st.session_state.expanded_stories = {st.session_state.selected_story}

# 8. Sidebar Directory: Direct Story & Character Bubbles (Tight Spacing)
st.sidebar.markdown("### Conversations")

for story_name, story_data in catalog.items():
    is_expanded = story_name in st.session_state.expanded_stories
    cover_b64 = get_image_base64(story_data.get("cover", ""))
    cover_html = f'<img class="book-bubble-thumb" src="{cover_b64}">' if cover_b64 else '<div class="book-bubble-fallback">📖</div>'
    
    # Story Bubble & Title Row
    col_b_thumb, col_b_btn = st.sidebar.columns([1, 4])
    with col_b_thumb:
        st.markdown(cover_html, unsafe_allow_html=True)
    with col_b_btn:
        st.markdown('<div class="sidebar-book-btn">', unsafe_allow_html=True)
        arrow = "▾" if is_expanded else "▸"
        if st.button(f"{arrow} {story_name}", key=f"book_toggle_{story_name}", use_container_width=True):
            if is_expanded:
                st.session_state.expanded_stories.remove(story_name)
            else:
                st.session_state.expanded_stories.add(story_name)
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # Indented Character Bubbles
    if is_expanded:
        for char_obj in story_data["characters"]:
            is_active = (char_obj["name"] == st.session_state.selected_char and story_name == st.session_state.selected_story)
            char_b64 = get_image_base64(char_obj.get("avatar", ""))
            
            thumb_class = "char-bubble-thumb-active" if is_active else "char-bubble-thumb"
            char_thumb_html = f'<img class="{thumb_class}" src="{char_b64}">' if char_b64 else '<div class="char-bubble-fallback">👤</div>'
            
            col_ind, col_c_thumb, col_c_btn = st.sidebar.columns([0.35, 0.9, 3.75])
            with col_c_thumb:
                st.markdown(char_thumb_html, unsafe_allow_html=True)
            with col_c_btn:
                btn_class = "sidebar-char-btn-active" if is_active else "sidebar-char-btn"
                st.markdown(f'<div class="{btn_class}">', unsafe_allow_html=True)
                
                label = f"💬 {char_obj['name']}" if is_active else char_obj["name"]
                if st.button(label, key=f"sel_{story_name}_{char_obj['name']}", use_container_width=True):
                    st.session_state.selected_story = story_name
                    st.session_state.selected_char = char_obj["name"]
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

# Retrieve Active Character Details
selected_story = st.session_state.selected_story
chars_in_story = catalog[selected_story]["characters"]
current_char = next((c for c in chars_in_story if c["name"] == st.session_state.selected_char), chars_in_story[0])
st.session_state.selected_char = current_char["name"]
avatar_b64 = get_image_base64(current_char.get("avatar", ""))

# 9. Locked Profile Card in Sidebar
avatar_portrait_html = f'<img class="light-profile-avatar" src="{avatar_b64}">' if avatar_b64 else '<div class="light-profile-avatar-fallback">📖</div>'
st.sidebar.markdown(f"""
<div class="locked-profile-anchor">
    <div class="light-profile-card">
        {avatar_portrait_html}
        <div class="light-profile-name">{current_char['name']}</div>
        <div class="light-profile-book">📖 {selected_story}</div>
        <div class="light-profile-bio">
            <b>About:</b><br>{current_char.get('tagline', '')}
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

with st.sidebar.container():
    st.markdown('<div class="clear-chat-container">', unsafe_allow_html=True)
    if st.button("🗑️ Clear Chat History", key="clear_chat_history_btn", use_container_width=True):
        now = get_hkt_time()
        st.session_state.character_chats[current_char["name"]] = [
            {"role": "assistant", "content": f"Hello! I am {current_char['name']}. What would you like to ask me?", "time": now}
        ]
        st.session_state.failed_prompts.pop(current_char["name"], None)
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# 10. Initialize Conversation
now_str = get_hkt_time()
if current_char["name"] not in st.session_state.character_chats:
    st.session_state.character_chats[current_char["name"]] = [
        {
            "role": "assistant",
            "content": f"Hello! I am {current_char['name']}. What would you like to ask me?",
            "time": now_str
        }
    ]

current_messages = st.session_state.character_chats[current_char["name"]]

# 11. Locked Top Header Bar with Glowing Green Status Dot
top_avatar_html = f'<img class="header-avatar" src="{avatar_b64}">' if avatar_b64 else '<div class="header-avatar-fallback">📖</div>'
st.markdown(f"""
<div class="chat-top-header">
    <div class="header-left">
        <span class="back-arrow-btn">←</span>
        <div class="header-titles">
            <h3>{current_char['name']}</h3>
            <span class="online-badge"><span class="status-dot-glow"></span> Online</span>
        </div>
    </div>
    {top_avatar_html}
</div>
""", unsafe_allow_html=True)

# 12. Starter Questions
starters = current_char.get("starter_questions", [])
if len(current_messages) <= 1 and starters:
    cols = st.columns(len(starters))
    for idx, question in enumerate(starters):
        if cols[idx].button(question, key=f"{current_char['name']}_chip_{idx}", use_container_width=True):
            st.session_state.pending_prompt = question
            st.rerun()

# 13. Render Chat Feed
for msg in current_messages:
    role = msg["role"]
    content = msg["content"]
    
    st.markdown(
        f'<div class="msg-row {role}"><div class="msg-bubble {role}">{content}</div></div>',
        unsafe_allow_html=True
    )

# 14. Persistent Retry Notification Bar
if current_char["name"] in st.session_state.failed_prompts:
    failed_text = st.session_state.failed_prompts[current_char["name"]]
    st.warning(f"Connection dropped on: '{failed_text}'")
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("🔄 Resend Message", key="retry_btn_action", use_container_width=True):
            st.session_state.pending_prompt = st.session_state.failed_prompts.pop(current_char["name"])
            st.rerun()
    with col2:
        if st.button("Dismiss", key="dismiss_btn_action", use_container_width=True):
            st.session_state.failed_prompts.pop(current_char["name"])
            st.rerun()

# 15. Integrated Bottom Chat Input with Natural Typing Pace
user_query = st.chat_input("Write a message...")
if "pending_prompt" in st.session_state:
    user_query = st.session_state.pop("pending_prompt")

if user_query:
    if not api_key:
        st.error("Please add OPENROUTER_API_KEY in Streamlit Secrets.")
        st.stop()

    current_time = get_hkt_time()

    # Save and display user message immediately
    st.session_state.character_chats[current_char["name"]].append({
        "role": "user",
        "content": user_query,
        "time": current_time
    })
    st.markdown(
        f'<div class="msg-row user"><div class="msg-bubble user">{user_query}</div></div>',
        unsafe_allow_html=True
    )

    # Clean roleplay instructions tailored for primary school learners
    system_instruction = (
        f"You are roleplaying as {current_char['name']} from the book '{selected_story}'.\n"
        f"{current_char['system_prompt']}\n\n"
        "Rules for speaking to the student:\n"
        "1. Speak directly in character using simple, everyday English words suitable for primary school students.\n"
        "2. Keep your answer brief: 2 to 3 sentences maximum.\n"
        "3. Do NOT repeat or echo the student's question.\n"
        "4. Output only your spoken words. Never write outlines, notes, or bullet points."
    )

    conversation_payload = [
        {"role": "system", "content": system_instruction}
    ]
    for m in st.session_state.character_chats[current_char["name"]][-8:]:
        conversation_payload.append({"role": m["role"], "content": m["content"]})

    # Realistic typing indicator display
    typing_box = st.empty()
    typing_box.markdown(f'''
    <div class="typing-pill">
        <span>✍️ {current_char["name"]} is typing...</span>
    </div>
    ''', unsafe_allow_html=True)

    # 1.4-second natural pause before words start streaming
    time.sleep(1.4)

    bubble_placeholder = st.empty()
    full_response_text = ""

    try:
        stream = client.chat.completions.create(
            model=MODEL_NAME,
            messages=conversation_payload,
            stream=True,
            temperature=0.7,
            max_tokens=150
        )
        
        has_started_typing = False
        for chunk in stream:
            content = chunk.choices[0].delta.content or ""
            if not content:
                continue

            for char in content:
                full_response_text += char
                time.sleep(0.015)  # 15ms per character typing cadence
                
                if not has_started_typing and full_response_text.strip():
                    typing_box.empty()
                    has_started_typing = True

                if has_started_typing:
                    bubble_placeholder.markdown(
                        f'<div class="msg-row assistant"><div class="msg-bubble assistant">{full_response_text}</div></div>',
                        unsafe_allow_html=True
                    )

        typing_box.empty()

        if full_response_text.strip():
            st.session_state.character_chats[current_char["name"]].append({
                "role": "assistant",
                "content": full_response_text.strip(),
                "time": current_time
            })
            st.session_state.failed_prompts.pop(current_char["name"], None)
        else:
            bubble_placeholder.empty()
            raise Exception("No response received from the model.")

    except Exception as e:
        typing_box.empty()
        bubble_placeholder.empty()
        
        if st.session_state.character_chats[current_char["name"]] and st.session_state.character_chats[current_char["name"]][-1]["role"] == "user":
            st.session_state.character_chats[current_char["name"]].pop()
            
        st.session_state.failed_prompts[current_char["name"]] = user_query
        st.rerun()
