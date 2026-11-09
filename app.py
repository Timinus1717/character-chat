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

# 4. Custom Dark Crimson Messenger CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }

    /* Ultra-dark canvas background */
    .stApp {
        background-color: #121318;
    }

    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 5.5rem !important;
        max-width: 680px !important;
    }

    /* Top Floating Chat Bar */
    .chat-top-bar {
        position: sticky;
        top: 0;
        z-index: 99;
        display: flex;
        align-items: center;
        background: #181a20;
        border: 1px solid #232630;
        padding: 10px 16px;
        border-radius: 20px;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
        margin-bottom: 14px;
    }
    .back-btn-mock {
        width: 36px;
        height: 36px;
        border-radius: 50%;
        background: #22252e;
        display: flex;
        align-items: center;
        justify-content: center;
        color: #9aa0b0;
        font-size: 16px;
        margin-right: 12px;
    }
    .top-avatar {
        width: 44px;
        height: 44px;
        border-radius: 50%;
        object-fit: cover;
        margin-right: 12px;
        border: 2px solid #ff4e50;
    }
    .top-avatar-fallback {
        width: 44px;
        height: 44px;
        border-radius: 50%;
        background: linear-gradient(135deg, #ff4e50 0%, #f02541 100%);
        color: white;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 20px;
        margin-right: 12px;
    }
    .top-info {
        flex-grow: 1;
    }
    .top-info h3 {
        margin: 0;
        color: #ffffff;
        font-size: 1.05rem;
        font-weight: 700;
        letter-spacing: -0.01em;
    }
    .top-info .status-subtext {
        margin: 0;
        color: #8b92a3;
        font-size: 0.78rem;
    }
    .top-call-mock {
        width: 36px;
        height: 36px;
        border-radius: 50%;
        background: rgba(255, 78, 80, 0.12);
        color: #ff4e50;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 16px;
    }

    /* "Today" Pill Chip */
    .date-separator {
        display: flex;
        justify-content: center;
        margin: 14px 0 16px 0;
    }
    .date-pill {
        background: #1c1e26;
        color: #8b92a3;
        font-size: 0.75rem;
        font-weight: 600;
        padding: 4px 14px;
        border-radius: 20px;
        border: 1px solid #262933;
    }

    /* Chat Message Bubbles */
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
        max-width: 82%;
        padding: 11px 16px 22px 16px;
        font-size: 0.94rem;
        line-height: 1.45;
        word-wrap: break-word;
        white-space: pre-wrap;
        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.25);
    }

    /* User Bubble: Vibrant Coral Red Gradient */
    .msg-bubble.user {
        background: linear-gradient(135deg, #ff4e50 0%, #f02541 100%);
        color: #ffffff;
        border-radius: 18px 18px 4px 18px;
    }

    /* Assistant Bubble: Dark Charcoal Card */
    .msg-bubble.assistant {
        background: #1e2027;
        color: #f1f2f6;
        border: 1px solid #282b35;
        border-radius: 18px 18px 18px 4px;
    }

    .bubble-timestamp {
        position: absolute;
        bottom: 5px;
        right: 12px;
        font-size: 0.68rem;
        font-weight: 500;
        opacity: 0.8;
    }
    .msg-bubble.user .bubble-timestamp {
        color: #ffe0e0;
    }
    .msg-bubble.assistant .bubble-timestamp {
        color: #8b92a3;
    }

    /* Typing Indicator Box */
    .typing-pill {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: #1c1e26;
        border: 1px solid #282b35;
        padding: 7px 14px;
        border-radius: 14px;
        margin-bottom: 10px;
        color: #ff4e50;
        font-size: 0.82rem;
        font-weight: 600;
    }

    /* Prompt Button Chips */
    .stButton button {
        background-color: #1a1c23 !important;
        color: #e2e8f0 !important;
        border: 1px solid #2d313d !important;
        border-radius: 14px !important;
        font-size: 0.84rem !important;
        font-weight: 500 !important;
        padding: 8px 12px !important;
        transition: all 0.2s ease !important;
    }
    .stButton button:hover {
        background: linear-gradient(135deg, #ff4e50 0%, #f02541 100%) !important;
        color: #ffffff !important;
        border-color: #ff4e50 !important;
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(255, 78, 80, 0.3) !important;
    }

    /* Sidebar Dark Theme Styling */
    [data-testid="stSidebar"] {
        background-color: #16181f;
        border-right: 1px solid #222530;
    }
    [data-testid="stSidebar"] h3 {
        color: #ffffff;
        font-weight: 700;
        letter-spacing: -0.02em;
    }

    /* Story Card Item in Sidebar */
    .sidebar-story-card {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 10px 12px;
        background: #1e2029;
        border-radius: 14px;
        border: 1px solid #282b38;
        margin-top: 12px;
        margin-bottom: 6px;
    }
    .sidebar-story-thumb {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        object-fit: cover;
        border: 2px solid #ff4e50;
        flex-shrink: 0;
    }
    .sidebar-story-fallback {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        background: #ff4e50;
        color: white;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 18px;
        flex-shrink: 0;
    }
    .sidebar-story-title {
        font-size: 0.90rem;
        font-weight: 600;
        color: #ffffff;
        line-height: 1.3;
    }

    /* Contact Row in Sidebar */
    .sidebar-char-thumb {
        width: 32px;
        height: 32px;
        border-radius: 50%;
        object-fit: cover;
        border: 1.5px solid #ff4e50;
        margin-top: 4px;
    }
    .sidebar-char-fallback {
        width: 32px;
        height: 32px;
        border-radius: 50%;
        background: #2a2d39;
        color: #ff4e50;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 15px;
        margin-top: 4px;
    }

    /* Sidebar Profile Card */
    .dark-profile-card {
        background: #1c1e26;
        border-radius: 18px;
        padding: 16px 14px;
        text-align: center;
        border: 1px solid #282b36;
        margin-top: 14px;
        box-shadow: 0 4px 14px rgba(0,0,0,0.3);
    }
    .dark-profile-avatar {
        width: 82px;
        height: 82px;
        border-radius: 50%;
        object-fit: cover;
        margin: 0 auto 10px auto;
        display: block;
        border: 3px solid #ff4e50;
        box-shadow: 0 4px 14px rgba(255, 78, 80, 0.25);
    }
    .dark-profile-avatar-fallback {
        width: 82px;
        height: 82px;
        border-radius: 50%;
        background: linear-gradient(135deg, #ff4e50 0%, #f02541 100%);
        color: white;
        font-size: 40px;
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 0 auto 10px auto;
    }
    .dark-profile-name {
        font-size: 1.05rem;
        font-weight: 700;
        color: #ffffff;
        margin-bottom: 2px;
    }
    .dark-profile-book {
        font-size: 0.78rem;
        color: #ff6b6b;
        font-weight: 500;
        margin-bottom: 10px;
    }
    .dark-profile-bio {
        background: #14151b;
        border: 1px solid #242732;
        border-radius: 12px;
        padding: 10px;
        font-size: 0.82rem;
        color: #a0a6b5;
        text-align: left;
        line-height: 1.45;
    }

    /* Streamlit Input field dark adaptation */
    [data-testid="stChatInput"] {
        background-color: #181a20 !important;
        border-radius: 24px !important;
        border: 1px solid #2a2d38 !important;
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

# 7. Persistent Memory Initialization
if "character_chats" not in st.session_state:
    st.session_state.character_chats = {}

if "failed_prompts" not in st.session_state:
    st.session_state.failed_prompts = {}

if "selected_story" not in st.session_state:
    st.session_state.selected_story = all_stories[0]

first_char_name = catalog[st.session_state.selected_story]["characters"][0]["name"]
if "selected_char" not in st.session_state:
    st.session_state.selected_char = first_char_name

# 8. Dark Contacts Directory (Sidebar)
st.sidebar.markdown("### 💬 Chats")

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
    
    with st.sidebar.expander(f"Characters in {story_name}", expanded=is_active_story):
        for char_obj in story_data["characters"]:
            char_b64 = get_image_base64(char_obj.get("avatar", ""))
            char_thumb = f'<img class="sidebar-char-thumb" src="{char_b64}">' if char_b64 else '<div class="sidebar-char-fallback">👤</div>'
            
            col_thumb, col_btn = st.columns([1, 4])
            with col_thumb:
                st.markdown(char_thumb, unsafe_allow_html=True)
            with col_btn:
                is_selected = (char_obj["name"] == st.session_state.selected_char and is_active_story)
                label = f"🔴 {char_obj['name']}" if is_selected else char_obj["name"]
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

# Profile Card for Selected Character
st.sidebar.markdown("---")
avatar_portrait_html = f'<img class="dark-profile-avatar" src="{avatar_b64}">' if avatar_b64 else '<div class="dark-profile-avatar-fallback">📖</div>'
st.sidebar.markdown(f"""
<div class="dark-profile-card">
    {avatar_portrait_html}
    <div class="dark-profile-name">{current_char['name']}</div>
    <div class="dark-profile-book">📖 {selected_story}</div>
    <div class="dark-profile-bio">
        <b>About:</b><br>{current_char.get('tagline', '')}
    </div>
</div>
""", unsafe_allow_html=True)

st.sidebar.write("")
if st.sidebar.button("🗑️ Clear Chat History", use_container_width=True):
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

# 10. Top Bar (Matching Mockup Navigation)
top_avatar_html = f'<img class="top-avatar" src="{avatar_b64}">' if avatar_b64 else '<div class="top-avatar-fallback">📖</div>'
st.markdown(f"""
<div class="chat-top-bar">
    <div class="back-btn-mock">←</div>
    {top_avatar_html}
    <div class="top-info">
        <h3>{current_char['name']}</h3>
        <p class="status-subtext">Online • {selected_story}</p>
    </div>
    <div class="top-call-mock">📞</div>
</div>
""", unsafe_allow_html=True)

# 11. "Today" Pill Chip
st.markdown("""
<div class="date-separator">
    <span class="date-pill">Today</span>
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
    time_str = msg.get("time", now_str)
    
    st.markdown(
        f'<div class="msg-row {role}"><div class="msg-bubble {role}">{content}<span class="bubble-timestamp">{time_str}</span></div></div>',
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

# 15. Message Input & Execution
user_query = st.chat_input(f"Type a message to {current_char['name']}...")
if "pending_prompt" in st.session_state:
    user_query = st.session_state.pop("pending_prompt")

if user_query:
    if not api_key:
        st.error("Please add OPENROUTER_API_KEY in Streamlit Secrets.")
        st.stop()

    current_time = get_hkt_time()

    # Save and display user message immediately in coral red bubble
    st.session_state.character_chats[current_char["name"]].append({
        "role": "user",
        "content": user_query,
        "time": current_time
    })
    st.markdown(
        f'<div class="msg-row user"><div class="msg-bubble user">{user_query}<span class="bubble-timestamp">{current_time}</span></div></div>',
        unsafe_allow_html=True
    )

    # Build prompt payload
    conversation_payload = [
        {"role": "system", "content": current_char["system_prompt"]}
    ]
    for m in st.session_state.character_chats[current_char["name"]]:
        conversation_payload.append({"role": m["role"], "content": m["content"]})

    # "Typing..." Pill indicator matching header mockup
    typing_box = st.empty()
    typing_box.markdown(f'''
    <div class="typing-pill">
        <span>{current_char["name"]} is typing...</span>
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
                    f'<div class="msg-row assistant"><div class="msg-bubble assistant">{response_text}<span class="bubble-timestamp">{current_time}</span></div></div>',
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
