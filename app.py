import os
import json
import re
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

# 4. Reliable Clean Output Sanitizer
def clean_ai_reply(text: str, user_prompt: str) -> str:
    """Strips thinking tags, meta-headers, and echoes."""
    if not text:
        return ""
    
    # Strip <think> blocks
    cleaned = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
    
    # Remove markdown analysis headers if any appear
    cleaned = re.sub(r'(?i)\d+\.\s*\*\*.*?(?:Analyze|Recall|Formulate|Persona|Context).*?\n', '', cleaned)
    cleaned = re.sub(r'(?i)\*.*?(?:User asks|Constraints|Target Audience).*?\n', '', cleaned)
    cleaned = cleaned.strip()

    # If the model simply echoed the user's prompt, invalidate it so it does not render
    if cleaned.strip().lower().strip('?"\'!.') == user_prompt.strip().lower().strip('?"\'!.'):
        return ""
        
    return cleaned

# 5. Sky-Blue CSS
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
        background-color: #eef7fc !important;
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
        background-color: #eef7fc !important;
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
        box-shadow: 0 8px 24px rgba(56, 189, 248, 0.16);
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
        font-size: 1.1rem;
        color: #64748b;
    }
    .header-titles h3 {
        margin: 0;
        font-size: 1.25rem;
        font-weight: 700;
        color: #1e293b !important;
        letter-spacing: -0.01em;
    }

    .online-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        margin: 0;
        font-size: 0.82rem;
        font-weight: 600;
        color: #059669 !important;
    }
    .status-dot-glow {
        width: 8px;
        height: 8px;
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
        box-shadow: 0 6px 16px rgba(14, 165, 233, 0.2);
        border: 2px solid #ffffff;
    }
    .header-avatar-fallback {
        width: 52px;
        height: 52px;
        border-radius: 50%;
        background: #0ea5e9;
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
        font-size: 0.96rem;
        line-height: 1.5;
        word-wrap: break-word;
        white-space: pre-wrap;
    }

    .msg-bubble.user {
        background: linear-gradient(135deg, #38bdf8 0%, #0284c7 100%) !important;
        color: #ffffff !important;
        border-radius: 22px 22px 4px 22px;
        box-shadow: 0 4px 14px rgba(14, 165, 233, 0.25);
    }

    .msg-bubble.assistant {
        background: #ffffff !important;
        color: #1e293b !important;
        border-radius: 22px 22px 22px 4px;
        box-shadow: 0 4px 14px rgba(148, 163, 184, 0.14);
        border: 1px solid rgba(226, 232, 240, 0.8);
    }

    .typing-pill {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: #ffffff !important;
        padding: 8px 16px;
        border-radius: 20px;
        margin-bottom: 12px;
        color: #0284c7 !important;
        font-size: 0.84rem;
        font-weight: 600;
        box-shadow: 0 2px 8px rgba(14, 165, 233, 0.12);
    }

    .block-container .stButton button {
        background-color: #ffffff !important;
        color: #0284c7 !important;
        border: 1.5px solid #bae6fd !important;
        border-radius: 20px !important;
        font-size: 0.85rem !important;
        font-weight: 600 !important;
        padding: 8px 14px !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 2px 6px rgba(56, 189, 248, 0.08) !important;
    }
    .block-container .stButton button:hover {
        background: #38bdf8 !important;
        color: #ffffff !important;
        border-color: #38bdf8 !important;
        transform: translateY(-1px);
        box-shadow: 0 6px 14px rgba(56, 189, 248, 0.25) !important;
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
        border: 2px solid #bae6fd !important;
        box-shadow: 0 10px 25px -4px rgba(56, 189, 248, 0.3), 0 4px 12px rgba(0, 0, 0, 0.06) !important;
        padding: 6px 10px 6px 18px !important;
        margin-bottom: 12px !important;
    }

    [data-testid="stChatInput"] > div,
    [data-testid="stChatInput"] textarea {
        background-color: #ffffff !important;
        color: #0f172a !important;
        font-size: 0.95rem !important;
        caret-color: #0284c7 !important;
    }
    [data-testid="stChatInput"] textarea::placeholder {
        color: #94a3b8 !important;
    }

    [data-testid="stChatInput"] button {
        background: linear-gradient(135deg, #38bdf8 0%, #0ea5e9 100%) !important;
        color: #ffffff !important;
        border-radius: 50% !important;
        width: 38px !important;
        height: 38px !important;
        border: none !important;
        box-shadow: 0 4px 12px rgba(14, 165, 233, 0.35) !important;
    }
    [data-testid="stChatInput"] button svg {
        fill: #ffffff !important;
    }

    [data-testid="stSidebar"] {
        background-color: #ffffff !important;
        border-right: 1.5px solid #e0f2fe !important;
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
    }

    .sidebar-story-card {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 9px 12px;
        background: #f0f9ff !important;
        border-radius: 16px;
        border: 1.5px solid #d0ecfc !important;
        margin-top: 10px;
        margin-bottom: 4px;
        box-shadow: 0 2px 6px rgba(56, 189, 248, 0.05);
    }
    .sidebar-story-thumb {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        object-fit: cover;
        border: 2px solid #38bdf8;
        flex-shrink: 0;
    }
    .sidebar-story-fallback {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        background: #38bdf8;
        color: white;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 18px;
        flex-shrink: 0;
    }
    .sidebar-story-title {
        font-size: 0.90rem;
        font-weight: 700;
        color: #0f172a !important;
        line-height: 1.25;
    }

    [data-testid="stExpander"] {
        background-color: #ffffff !important;
        border: 1.5px solid #d0ecfc !important;
        border-radius: 14px !important;
        overflow: hidden !important;
        margin-bottom: 12px !important;
        box-shadow: 0 2px 8px rgba(56, 189, 248, 0.06) !important;
    }
    [data-testid="stExpander"] details {
        background-color: #ffffff !important;
        border: none !important;
    }
    [data-testid="stExpander"] summary,
    [data-testid="stExpander"] details summary,
    [data-testid="stExpander"] details[open] summary {
        background-color: #f0f9ff !important;
        color: #0284c7 !important;
        font-weight: 700 !important;
        font-size: 0.86rem !important;
        padding: 8px 12px !important;
        border-bottom: 1px solid #e0f2fe !important;
    }
    [data-testid="stExpander"] summary:hover {
        background-color: #e0f2fe !important;
        color: #0369a1 !important;
    }
    [data-testid="stExpander"] summary svg,
    [data-testid="stExpander"] summary span {
        fill: #0284c7 !important;
        color: #0284c7 !important;
    }

    [data-testid="stExpander"] div[data-testid="stExpanderDetails"] {
        background-color: #f8fafc !important;
        padding: 8px 8px !important;
    }

    .sidebar-char-thumb {
        width: 32px;
        height: 32px;
        border-radius: 50%;
        object-fit: cover;
        border: 1.5px solid #38bdf8;
        margin-top: 3px;
    }
    .sidebar-char-fallback {
        width: 32px;
        height: 32px;
        border-radius: 50%;
        background: #e0f2fe;
        color: #0284c7;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 14px;
        margin-top: 3px;
    }

    [data-testid="stSidebar"] [data-testid="stExpander"] .stButton button {
        background-color: #ffffff !important;
        color: #1e293b !important;
        border: 1.5px solid #e2e8f0 !important;
        border-radius: 12px !important;
        font-size: 0.82rem !important;
        font-weight: 600 !important;
        padding: 6px 10px !important;
        white-space: normal !important;
        word-break: break-word !important;
        height: auto !important;
        min-height: 36px !important;
        line-height: 1.25 !important;
        text-align: left !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04) !important;
        transition: all 0.2s ease !important;
    }
    [data-testid="stSidebar"] [data-testid="stExpander"] .stButton button:hover {
        background-color: #e0f2fe !important;
        color: #0284c7 !important;
        border-color: #38bdf8 !important;
        transform: translateY(-1px) !important;
    }

    div[data-testid="stElementContainer"]:has(.locked-profile-anchor),
    .element-container:has(.locked-profile-anchor) {
        position: sticky !important;
        bottom: 0 !important;
        z-index: 1000 !important;
        background: #ffffff !important;
        padding-top: 10px !important;
        padding-bottom: 8px !important;
        margin-top: auto !important;
        box-shadow: 0 -12px 24px -4px rgba(2, 132, 199, 0.08) !important;
        border-top: 1.5px solid #e0f2fe !important;
    }

    .light-profile-card {
        background: #f8fafc !important;
        border-radius: 18px;
        padding: 12px 10px;
        text-align: center;
        border: 1.5px solid #e2e8f0 !important;
    }
    .light-profile-avatar {
        width: 64px;
        height: 64px;
        border-radius: 50%;
        object-fit: cover;
        margin: 0 auto 6px auto;
        display: block;
        border: 2.5px solid #38bdf8;
        box-shadow: 0 4px 12px rgba(56, 189, 248, 0.25);
    }
    .light-profile-avatar-fallback {
        width: 64px;
        height: 64px;
        border-radius: 50%;
        background: #38bdf8;
        color: white;
        font-size: 30px;
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 0 auto 6px auto;
    }
    .light-profile-name {
        font-size: 0.95rem;
        font-weight: 700;
        color: #0f172a !important;
        margin-bottom: 2px;
    }
    .light-profile-book {
        font-size: 0.74rem;
        color: #0284c7 !important;
        font-weight: 600;
        margin-bottom: 6px;
    }
    .light-profile-bio {
        background: #ffffff !important;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 8px 10px;
        font-size: 0.78rem;
        color: #334155 !important;
        text-align: left;
        line-height: 1.4;
    }

    .clear-chat-container .stButton button {
        background-color: #ffffff !important;
        color: #e11d48 !important;
        border: 1.5px solid #fecdd3 !important;
        border-radius: 20px !important;
        font-size: 0.80rem !important;
        font-weight: 600 !important;
        padding: 6px 12px !important;
        margin-top: 6px !important;
        transition: all 0.2s ease !important;
    }
    .clear-chat-container .stButton button:hover {
        background-color: #ffe4e6 !important;
        border-color: #fb7185 !important;
        color: #be123c !important;
    }
</style>
""", unsafe_allow_html=True)

# 6. OpenRouter Connection
api_key = st.secrets.get("OPENROUTER_API_KEY", "")
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key or "missing_key"
)

# Use reliable conversational free model
MODEL_NAME = "meta-llama/llama-3.3-70b-instruct:free"

# 7. Load Catalog
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

# 8. Persistent Session Initialization
if "character_chats" not in st.session_state:
    st.session_state.character_chats = {}

if "failed_prompts" not in st.session_state:
    st.session_state.failed_prompts = {}

if "selected_story" not in st.session_state:
    st.session_state.selected_story = all_stories[0]

first_char_name = catalog[st.session_state.selected_story]["characters"][0]["name"]
if "selected_char" not in st.session_state:
    st.session_state.selected_char = first_char_name

# 9. Sidebar Directory
st.sidebar.markdown("### Conversations")

for story_name, story_data in catalog.items():
    is_active_story = (story_name == st.session_state.selected_story)
    cover_b64 = get_image_base64(story_data.get("cover", ""))
    cover_html = f'<img class="sidebar-story-thumb" src="{cover_b64}">' if cover_b64 else '<div class="sidebar-story-fallback">📖</div>'
    
    st.sidebar.markdown(f"""
    <div class="sidebar-story-card">
        {cover_html}
        <div class="sidebar-story-title">{story_name}</div>
    </div>
    """, unsafe_allow_html=True)
    
    with st.sidebar.expander("Characters", expanded=is_active_story):
        for char_obj in story_data["characters"]:
            char_b64 = get_image_base64(char_obj.get("avatar", ""))
            char_thumb = f'<img class="sidebar-char-thumb" src="{char_b64}">' if char_b64 else '<div class="sidebar-char-fallback">👤</div>'
            
            col_thumb, col_btn = st.columns([1, 4])
            with col_thumb:
                st.markdown(char_thumb, unsafe_allow_html=True)
            with col_btn:
                is_selected = (char_obj["name"] == st.session_state.selected_char and is_active_story)
                label = f"💬 {char_obj['name']}" if is_selected else char_obj["name"]
                if st.button(label, key=f"sel_{story_name}_{char_obj['name']}", use_container_width=True):
                    st.session_state.selected_story = story_name
                    st.session_state.selected_char = char_obj["name"]
                    st.rerun()

# Retrieve Active Character Details
selected_story = st.session_state.selected_story
chars_in_story = catalog[selected_story]["characters"]
current_char = next((c for c in chars_in_story if c["name"] == st.session_state.selected_char), chars_in_story[0])
st.session_state.selected_char = current_char["name"]
avatar_b64 = get_image_base64(current_char.get("avatar", ""))

# Locked Profile Card in Sidebar
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

# 10. Initialize Conversation & Purge Echoes or Analysis Leaks
now_str = get_hkt_time()
if current_char["name"] not in st.session_state.character_chats:
    st.session_state.character_chats[current_char["name"]] = [
        {
            "role": "assistant",
            "content": f"Hello! I am {current_char['name']}. What would you like to ask me?",
            "time": now_str
        }
    ]

# Purge corrupted messages and echo loops from existing session state
cleaned_chat = []
for idx, m in enumerate(st.session_state.character_chats[current_char["name"]]):
    content = m.get("content", "").strip()
    if not content:
        continue
    # Drop previous analysis breakdown leaks
    if "Analyze the Request" in content or "Recall Character" in content:
        continue
    # Drop echoing messages where assistant duplicated the user's previous line
    if m["role"] == "assistant" and idx > 0:
        prev = st.session_state.character_chats[current_char["name"]][idx - 1]
        if prev["role"] == "user" and prev["content"].strip().lower() == content.strip().lower():
            continue
    cleaned_chat.append(m)

if not cleaned_chat or cleaned_chat[0]["role"] != "assistant":
    cleaned_chat.insert(0, {
        "role": "assistant",
        "content": f"Hello! I am {current_char['name']}. What would you like to ask me?",
        "time": now_str
    })

st.session_state.character_chats[current_char["name"]] = cleaned_chat
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

# 15. Integrated Bottom Chat Input
user_query = st.chat_input("Write a message...")
if "pending_prompt" in st.session_state:
    user_query = st.session_state.pop("pending_prompt")

if user_query:
    if not api_key:
        st.error("Please add OPENROUTER_API_KEY in Streamlit Secrets.")
        st.stop()

    current_time = get_hkt_time()

    # Save and display user message
    st.session_state.character_chats[current_char["name"]].append({
        "role": "user",
        "content": user_query,
        "time": current_time
    })
    st.markdown(
        f'<div class="msg-row user"><div class="msg-bubble user">{user_query}</div></div>',
        unsafe_allow_html=True
    )

    # Conversational roleplay prompt
    system_instruction = (
        f"You are {current_char['name']} from '{selected_story}'.\n"
        f"{current_char['system_prompt']}\n\n"
        "Guidelines for speaking with primary school students:\n"
        "- Reply directly in character using friendly, simple, everyday English words.\n"
        "- Keep your answer short (2 to 3 sentences maximum).\n"
        "- Do NOT repeat the user's question.\n"
        "- Do NOT provide analysis, notes, or bullet points."
    )

    conversation_payload = [
        {"role": "system", "content": system_instruction}
    ]
    # Send clean recent messages
    for m in st.session_state.character_chats[current_char["name"]][-6:]:
        conversation_payload.append({"role": m["role"], "content": m["content"]})

    # Cyan "Typing..." Pill indicator
    typing_box = st.empty()
    typing_box.markdown(f'''
    <div class="typing-pill">
        <span>✍️ {current_char["name"]} is typing...</span>
    </div>
    ''', unsafe_allow_html=True)

    bubble_placeholder = st.empty()
    raw_response_text = ""

    try:
        # Request from conversational model with fallback to openrouter/free
        try:
            stream = client.chat.completions.create(
                model=MODEL_NAME,
                messages=conversation_payload,
                stream=True,
                temperature=0.7,
                max_tokens=150
            )
        except Exception:
            stream = client.chat.completions.create(
                model="openrouter/free",
                messages=conversation_payload,
                stream=True,
                temperature=0.7,
                max_tokens=150
            )
        
        has_started_typing = False
        for chunk in stream:
            content = chunk.choices[0].delta.content or ""
            raw_response_text += content
            
            clean_display = clean_ai_reply(raw_response_text, user_query)
            
            if not has_started_typing and clean_display.strip():
                typing_box.empty()
                has_started_typing = True

            if has_started_typing and clean_display.strip():
                bubble_placeholder.markdown(
                    f'<div class="msg-row assistant"><div class="msg-bubble assistant">{clean_display}</div></div>',
                    unsafe_allow_html=True
                )

        typing_box.empty()
        final_clean_response = clean_ai_reply(raw_response_text, user_query)

        if final_clean_response.strip():
            st.session_state.character_chats[current_char["name"]].append({
                "role": "assistant",
                "content": final_clean_response,
                "time": current_time
            })
            st.session_state.failed_prompts.pop(current_char["name"], None)
        else:
            bubble_placeholder.empty()
            raise Exception("AI response was blank or invalid. Please try again.")

    except Exception as e:
        typing_box.empty()
        bubble_placeholder.empty()
        
        if st.session_state.character_chats[current_char["name"]] and st.session_state.character_chats[current_char["name"]][-1]["role"] == "user":
            st.session_state.character_chats[current_char["name"]].pop()
            
        st.session_state.failed_prompts[current_char["name"]] = user_query
        st.rerun()
