import os
import json
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

# 4. Sky-Blue & Pure White Minimalist CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }

    /* Outer application canvas */
    .stApp {
        background-color: #38bdf8;
        background: linear-gradient(145deg, #38bdf8 0%, #0ea5e9 100%);
    }

    /* Main chat container styled as a modern rounded card */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 6rem !important;
        max-width: 640px !important;
        background-color: #eef7fc;
        border-radius: 36px;
        box-shadow: 0 20px 40px rgba(2, 132, 199, 0.25);
        margin-top: 1.5rem;
        margin-bottom: 2rem;
        min-height: 85vh;
        border: 4px solid #ffffff;
    }

    /* Crisp White Curved Top Bar */
    .chat-top-header {
        position: sticky;
        top: 0;
        z-index: 99;
        display: flex;
        align-items: center;
        justify-content: space-between;
        background: #ffffff;
        padding: 14px 22px;
        border-radius: 28px;
        box-shadow: 0 6px 18px rgba(56, 189, 248, 0.08);
        margin-bottom: 18px;
    }
    .header-left {
        display: flex;
        align-items: center;
        gap: 12px;
    }
    .back-arrow-btn {
        font-size: 1.1rem;
        color: #64748b;
        cursor: pointer;
    }
    .header-titles h3 {
        margin: 0;
        font-size: 1.25rem;
        font-weight: 700;
        color: #1e293b;
        letter-spacing: -0.01em;
    }
    .header-titles .online-badge {
        margin: 0;
        font-size: 0.82rem;
        font-weight: 600;
        color: #38bdf8;
    }
    .header-avatar {
        width: 54px;
        height: 54px;
        border-radius: 50%;
        object-fit: cover;
        box-shadow: 0 6px 16px rgba(14, 165, 233, 0.2);
        border: 2px solid #ffffff;
    }
    .header-avatar-fallback {
        width: 54px;
        height: 54px;
        border-radius: 50%;
        background: #0ea5e9;
        color: white;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 24px;
        box-shadow: 0 6px 16px rgba(14, 165, 233, 0.2);
    }

    /* Message Bubbles */
    .msg-row {
        display: flex;
        width: 100%;
        margin-bottom: 12px;
    }
    .msg-row.user {
        justify-content: flex-end;
    }
    .msg-row.assistant {
        justify-content: flex-start;
    }

    .msg-bubble {
        position: relative;
        max-width: 78%;
        padding: 12px 18px;
        font-size: 0.94rem;
        line-height: 1.45;
        word-wrap: break-word;
        white-space: pre-wrap;
    }

    /* User Bubble: Vibrant Sky Blue Pill */
    .msg-bubble.user {
        background: #4fc3f7;
        background: linear-gradient(135deg, #4fc3f7 0%, #0ea5e9 100%);
        color: #ffffff;
        border-radius: 20px 20px 4px 20px;
        box-shadow: 0 4px 14px rgba(14, 165, 233, 0.25);
    }

    /* Character Bubble: Pure White Pill */
    .msg-bubble.assistant {
        background: #ffffff;
        color: #334155;
        border-radius: 20px 20px 20px 4px;
        box-shadow: 0 4px 12px rgba(148, 163, 184, 0.08);
    }

    /* Typing Status Chip */
    .typing-pill {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: #ffffff;
        padding: 8px 16px;
        border-radius: 20px;
        margin-bottom: 12px;
        color: #0ea5e9;
        font-size: 0.82rem;
        font-weight: 600;
        box-shadow: 0 2px 8px rgba(14, 165, 233, 0.12);
    }

    /* Starter Question Buttons */
    .stButton button {
        background-color: #ffffff !important;
        color: #0284c7 !important;
        border: 1px solid #bae6fd !important;
        border-radius: 20px !important;
        font-size: 0.84rem !important;
        font-weight: 600 !important;
        padding: 8px 14px !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 2px 6px rgba(56, 189, 248, 0.08) !important;
    }
    .stButton button:hover {
        background: #38bdf8 !important;
        color: #ffffff !important;
        border-color: #38bdf8 !important;
        transform: translateY(-1px);
        box-shadow: 0 6px 14px rgba(56, 189, 248, 0.25) !important;
    }

    /* Integrate Streamlit Chat Input Directly Into the Chat Body */
    [data-testid="stBottom"] {
        background-color: transparent !important;
        border: none !important;
    }
    [data-testid="stBottom"] > div {
        background-color: transparent !important;
        border: none !important;
    }

    [data-testid="stChatInput"] {
        background-color: #ffffff !important;
        border-radius: 36px !important;
        border: 1.5px solid #d0ecfc !important;
        box-shadow: 0 10px 25px -4px rgba(56, 189, 248, 0.25), 0 4px 10px rgba(0, 0, 0, 0.04) !important;
        padding: 6px 10px 6px 18px !important;
        margin-bottom: 8px !important;
    }

    [data-testid="stChatInput"] textarea {
        color: #1e293b !important;
        font-size: 0.94rem !important;
    }

    [data-testid="stChatInput"] textarea::placeholder {
        color: #94a3b8 !important;
    }

    /* Cyan Circular Send Button */
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

    /* Sidebar "Conversations" Styling */
    [data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e0f2fe;
    }
    [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
        color: #0f172a;
        font-weight: 700;
        letter-spacing: -0.02em;
    }

    .sidebar-story-card {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 10px 12px;
        background: #f0f9ff;
        border-radius: 16px;
        border: 1px solid #e0f2fe;
        margin-top: 10px;
        margin-bottom: 6px;
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
        color: #0f172a;
    }

    .sidebar-char-thumb {
        width: 34px;
        height: 34px;
        border-radius: 50%;
        object-fit: cover;
        border: 1.5px solid #38bdf8;
        margin-top: 4px;
    }
    .sidebar-char-fallback {
        width: 34px;
        height: 34px;
        border-radius: 50%;
        background: #e0f2fe;
        color: #0284c7;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 15px;
        margin-top: 4px;
    }

    /* Clean Sidebar Profile Card */
    .light-profile-card {
        background: #f8fafc;
        border-radius: 20px;
        padding: 16px 14px;
        text-align: center;
        border: 1px solid #e2e8f0;
        margin-top: 14px;
    }
    .light-profile-avatar {
        width: 78px;
        height: 78px;
        border-radius: 50%;
        object-fit: cover;
        margin: 0 auto 10px auto;
        display: block;
        border: 3px solid #38bdf8;
        box-shadow: 0 4px 14px rgba(56, 189, 248, 0.25);
    }
    .light-profile-avatar-fallback {
        width: 78px;
        height: 78px;
        border-radius: 50%;
        background: #38bdf8;
        color: white;
        font-size: 38px;
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 0 auto 10px auto;
    }
    .light-profile-name {
        font-size: 1.05rem;
        font-weight: 700;
        color: #0f172a;
        margin-bottom: 2px;
    }
    .light-profile-book {
        font-size: 0.78rem;
        color: #0284c7;
        font-weight: 600;
        margin-bottom: 10px;
    }
    .light-profile-bio {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 10px;
        font-size: 0.82rem;
        color: #475569;
        text-align: left;
        line-height: 1.45;
    }
</style>
""", unsafe_allow_html=True)

# 5. OpenRouter Connection
api_key = st.secrets.get("OPENROUTER_API_KEY", "")
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key or "missing_key"
)

MODEL_NAME = "openrouter/free"

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

# 8. "Conversations" Sidebar
st.sidebar.markdown("### Conversations")[cite: 7]

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
    
    with st.sidebar.expander(f"Characters", expanded=is_active_story):
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

# Profile Card in Sidebar
st.sidebar.markdown("---")
avatar_portrait_html = f'<img class="light-profile-avatar" src="{avatar_b64}">' if avatar_b64 else '<div class="light-profile-avatar-fallback">📖</div>'
st.sidebar.markdown(f"""
<div class="light-profile-card">
    {avatar_portrait_html}
    <div class="light-profile-name">{current_char['name']}</div>
    <div class="light-profile-book">📖 {selected_story}</div>
    <div class="light-profile-bio">
        <b>About:</b><br>{current_char.get('tagline', '')}
    </div>
</div>
""", unsafe_allow_html=True)

st.sidebar.write("")
if st.sidebar.button("🗑️ Clear History", use_container_width=True):
    now = get_hkt_time()
    st.session_state.character_chats[current_char["name"]] = [
        {"role": "assistant", "content": f"Hello! I am {current_char['name']}. What would you like to ask me?", "time": now}
    ]
    st.session_state.failed_prompts.pop(current_char["name"], None)
    st.rerun()

# 9. Persistent Conversation Initialization
now_str = get_hkt_time()
if current_char["name"] not in st.session_state.character_chats:
    st.session_state.character_chats[current_char["name"]] = [
        {
            "role": "assistant",
            "content": f"Hello! I am {current_char['name']}. What would you like to ask me?",
            "time": now_str
        }
    ]

# Purge any empty messages
st.session_state.character_chats[current_char["name"]] = [
    m for m in st.session_state.character_chats[current_char["name"]] 
    if m.get("content", "").strip() != ""
]
current_messages = st.session_state.character_chats[current_char["name"]]

# 10. Top Bar (Curved Header Card Matching Mockup)
top_avatar_html = f'<img class="header-avatar" src="{avatar_b64}">' if avatar_b64 else '<div class="header-avatar-fallback">📖</div>'
st.markdown(f"""
<div class="chat-top-header">
    <div class="header-left">
        <span class="back-arrow-btn">←</span>
        <div class="header-titles">
            <h3>{current_char['name']}</h3>
            <span class="online-badge">Online</span>
        </div>
    </div>
    {top_avatar_html}
</div>
""", unsafe_allow_html=True)

# 11. Starter Questions
starters = current_char.get("starter_questions", [])
if len(current_messages) <= 1 and starters:
    cols = st.columns(len(starters))
    for idx, question in enumerate(starters):
        if cols[idx].button(question, key=f"{current_char['name']}_chip_{idx}", use_container_width=True):
            st.session_state.pending_prompt = question
            st.rerun()

# 12. Render Clean Pill Chat Feed
for msg in current_messages:
    role = msg["role"]
    content = msg["content"]
    
    st.markdown(
        f'<div class="msg-row {role}"><div class="msg-bubble {role}">{content}</div></div>',
        unsafe_allow_html=True
    )

# 13. Persistent Retry Notification Bar
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

# 14. Integrated Bottom Chat Input
user_query = st.chat_input(f"Write a message...")[cite: 7]
if "pending_prompt" in st.session_state:
    user_query = st.session_state.pop("pending_prompt")

if user_query:
    if not api_key:
        st.error("Please add OPENROUTER_API_KEY in Streamlit Secrets.")
        st.stop()

    current_time = get_hkt_time()

    # Save and display user message in sky-blue bubble
    st.session_state.character_chats[current_char["name"]].append({
        "role": "user",
        "content": user_query,
        "time": current_time
    })
    st.markdown(
        f'<div class="msg-row user"><div class="msg-bubble user">{user_query}</div></div>',
        unsafe_allow_html=True
    )

    # Build prompt payload
    conversation_payload = [
        {"role": "system", "content": current_char["system_prompt"]}
    ]
    for m in st.session_state.character_chats[current_char["name"]]:
        conversation_payload.append({"role": m["role"], "content": m["content"]})

    # Cyan "Typing..." Pill indicator
    typing_box = st.empty()
    typing_box.markdown(f'''
    <div class="typing-pill">
        <span>✍️ {current_char["name"]} is typing...</span>
    </div>
    ''', unsafe_allow_html=True)

    bubble_placeholder = st.empty()
    response_text = ""

    try:
        stream = client.chat.completions.create(
            model=MODEL_NAME,
            messages=conversation_payload,
            stream=True,
            temperature=0.7,
            max_tokens=250
        )
        
        has_started_typing = False
        for chunk in stream:
            content = chunk.choices[0].delta.content or ""
            response_text += content
            
            if not has_started_typing and response_text.strip():
                typing_box.empty()
                has_started_typing = True

            if has_started_typing:
                bubble_placeholder.markdown(
                    f'<div class="msg-row assistant"><div class="msg-bubble assistant">{response_text}</div></div>',
                    unsafe_allow_html=True
                )

        typing_box.empty()

        if response_text.strip():
            st.session_state.character_chats[current_char["name"]].append({
                "role": "assistant",
                "content": response_text,
                "time": current_time
            })
            st.session_state.failed_prompts.pop(current_char["name"], None)
        else:
            bubble_placeholder.empty()
            raise Exception("AI returned empty text. Service might be busy.")

    except Exception as e:
        typing_box.empty()
        bubble_placeholder.empty()
        
        if st.session_state.character_chats[current_char["name"]] and st.session_state.character_chats[current_char["name"]][-1]["role"] == "user":
            st.session_state.character_chats[current_char["name"]].pop()
            
        st.session_state.failed_prompts[current_char["name"]] = user_query
        st.rerun()
