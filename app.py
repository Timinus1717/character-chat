import os
import json
import base64
from datetime import datetime, timezone, timedelta
import streamlit as st
from openai import OpenAI

# 1. Page Configuration
st.set_page_config(
    page_title="Chronicle • Story Chat",
    page_icon="✨",
    layout="centered",
    initial_sidebar_state="expanded"
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 2. Hong Kong Time Helper (UTC+8)
def get_hkt_time():
    hkt_zone = timezone(timedelta(hours=8))
    return datetime.now(hkt_zone).strftime("%I:%M %p")

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

# 4. Modern High-Tech / Apple Glassmorphic CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }

    /* Ambient, subtle mesh gradient background */
    .stApp {
        background: radial-gradient(at 0% 0%, #f1f5f9 0px, transparent 50%),
                    radial-gradient(at 100% 0%, #e2e8f0 0px, transparent 50%),
                    radial-gradient(at 50% 100%, #f8fafc 0px, #edf2f7 100%);
        background-attachment: fixed;
    }

    .block-container {
        padding-top: 1.2rem !important;
        padding-bottom: 6rem !important;
        max-width: 780px !important;
    }

    /* Floating Frosted Glass Header */
    .hero-header {
        position: sticky;
        top: 0;
        z-index: 99;
        display: flex;
        align-items: center;
        background: rgba(255, 255, 255, 0.78);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid rgba(226, 232, 240, 0.9);
        padding: 12px 20px;
        border-radius: 20px;
        box-shadow: 0 8px 24px -4px rgba(15, 23, 42, 0.06);
        margin-bottom: 22px;
    }
    .hero-avatar {
        width: 52px;
        height: 52px;
        border-radius: 16px;
        object-fit: cover;
        margin-right: 16px;
        box-shadow: 0 4px 12px rgba(15, 23, 42, 0.12);
        border: 1px solid rgba(255, 255, 255, 0.8);
    }
    .hero-avatar-fallback {
        width: 52px;
        height: 52px;
        border-radius: 16px;
        background: linear-gradient(135deg, #0f172a 0%, #334155 100%);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 24px;
        margin-right: 16px;
        color: white;
    }
    .hero-info h3 {
        margin: 0;
        color: #0f172a;
        font-size: 1.15rem;
        font-weight: 700;
        letter-spacing: -0.02em;
    }
    .hero-badge-row {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-top: 3px;
    }
    .hero-tag {
        font-size: 0.75rem;
        font-weight: 600;
        color: #475569;
        background: #f1f5f9;
        padding: 2px 8px;
        border-radius: 6px;
        border: 1px solid #e2e8f0;
    }
    .live-indicator {
        display: flex;
        align-items: center;
        gap: 5px;
        font-size: 0.75rem;
        font-weight: 600;
        color: #059669;
    }
    .pulse-dot {
        width: 7px;
        height: 7px;
        background-color: #10b981;
        border-radius: 50%;
        box-shadow: 0 0 0 2px rgba(16, 185, 129, 0.2);
    }

    /* Message Stream */
    .msg-row {
        display: flex;
        width: 100%;
        margin-bottom: 16px;
    }
    .msg-row.user {
        justify-content: flex-end;
    }
    .msg-row.assistant {
        justify-content: flex-start;
    }

    .msg-card {
        position: relative;
        max-width: 80%;
        padding: 12px 18px 24px 18px;
        font-size: 0.95rem;
        line-height: 1.55;
        border-radius: 18px;
        box-shadow: 0 2px 8px rgba(15, 23, 42, 0.04);
        word-wrap: break-word;
        white-space: pre-wrap;
    }

    /* Student Message Card: Deep Obsidian Glass */
    .msg-card.user {
        background: #0f172a;
        color: #f8fafc;
        border-bottom-right-radius: 4px;
        box-shadow: 0 4px 14px rgba(15, 23, 42, 0.16);
    }

    /* Character Message Card: Luminous White Card with crisp accent border */
    .msg-card.assistant {
        background: #ffffff;
        color: #1e293b;
        border-bottom-left-radius: 4px;
        border: 1px solid #e2e8f0;
    }

    .msg-time {
        position: absolute;
        bottom: 6px;
        right: 12px;
        font-size: 0.68rem;
        font-weight: 500;
        opacity: 0.7;
    }

    /* Pulsing Typing Indicator */
    .typing-card {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: rgba(255, 255, 255, 0.9);
        border: 1px solid #e2e8f0;
        padding: 8px 14px;
        border-radius: 14px;
        margin-bottom: 12px;
        color: #64748b;
        font-size: 0.82rem;
        font-weight: 500;
    }
    .dot {
        width: 6px;
        height: 6px;
        background-color: #64748b;
        border-radius: 50%;
        display: inline-block;
        animation: pulse 1.4s infinite ease-in-out both;
    }
    .dot:nth-child(1) { animation-delay: -0.32s; }
    .dot:nth-child(2) { animation-delay: -0.16s; }
    @keyframes pulse {
        0%, 80%, 100% { transform: scale(0.6); opacity: 0.4; }
        40% { transform: scale(1); opacity: 1; }
    }

    /* Interactive Starter Question Chips */
    .stButton button {
        background: #ffffff !important;
        color: #334155 !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 12px !important;
        font-size: 0.85rem !important;
        font-weight: 600 !important;
        padding: 8px 14px !important;
        transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
        box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04) !important;
    }
    .stButton button:hover {
        background: #0f172a !important;
        color: #ffffff !important;
        border-color: #0f172a !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 16px -2px rgba(15, 23, 42, 0.15) !important;
    }

    /* Modern Sidebar Shell */
    [data-testid="stSidebar"] {
        background: #f8fafc;
        border-right: 1px solid #e2e8f0;
    }

    /* Sidebar Story Header Block */
    .story-module {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 8px 10px;
        background: #ffffff;
        border-radius: 14px;
        border: 1px solid #e2e8f0;
        margin-top: 10px;
        margin-bottom: 6px;
        box-shadow: 0 1px 2px rgba(15, 23, 42, 0.03);
    }
    .story-thumb {
        width: 38px;
        height: 38px;
        border-radius: 10px;
        object-fit: cover;
        border: 1px solid #e2e8f0;
        flex-shrink: 0;
    }
    .story-thumb-fallback {
        width: 38px;
        height: 38px;
        border-radius: 10px;
        background: #e2e8f0;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 18px;
        flex-shrink: 0;
    }
    .story-title {
        font-size: 0.88rem;
        font-weight: 600;
        color: #0f172a;
        line-height: 1.3;
    }

    /* Character Sub-item Thumbnail */
    .char-pill-avatar {
        width: 30px;
        height: 30px;
        border-radius: 8px;
        object-fit: cover;
        border: 1px solid #cbd5e1;
        margin-top: 4px;
    }
    .char-pill-fallback {
        width: 30px;
        height: 30px;
        border-radius: 8px;
        background: #f1f5f9;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 14px;
        margin-top: 4px;
    }

    /* Elegant Character Profile Card */
    .profile-card {
        background: #ffffff;
        border-radius: 18px;
        padding: 18px 14px;
        text-align: center;
        box-shadow: 0 4px 16px -2px rgba(15, 23, 42, 0.06);
        border: 1px solid #e2e8f0;
        margin-top: 14px;
    }
    .profile-portrait {
        width: 82px;
        height: 82px;
        border-radius: 20px;
        object-fit: cover;
        margin: 0 auto 10px auto;
        display: block;
        box-shadow: 0 4px 14px rgba(15, 23, 42, 0.12);
        border: 2px solid #ffffff;
    }
    .profile-portrait-fallback {
        width: 82px;
        height: 82px;
        border-radius: 20px;
        background: #0f172a;
        color: white;
        font-size: 38px;
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 0 auto 10px auto;
    }
    .profile-name {
        font-size: 1.05rem;
        font-weight: 700;
        color: #0f172a;
        margin-bottom: 2px;
        letter-spacing: -0.01em;
    }
    .profile-source {
        font-size: 0.78rem;
        color: #64748b;
        font-weight: 500;
        margin-bottom: 12px;
    }
    .profile-tagline {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 10px 12px;
        font-size: 0.82rem;
        color: #334155;
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

# 8. Clean Modern Sidebar Catalog
st.sidebar.markdown("### 📚 Story Library")

# Render each story module
for story_name, story_data in catalog.items():
    is_active_story = (story_name == st.session_state.selected_story)
    cover_b64 = get_image_base64(story_data.get("cover", ""))
    cover_html = f'<img class="story-thumb" src="{cover_b64}">' if cover_b64 else '<div class="story-thumb-fallback">📖</div>'
    
    st.sidebar.markdown(f"""
    <div class="story-module">
        {cover_html}
        <div class="story-title">{story_name}</div>
    </div>
    """, unsafe_allow_html=True)
    
    with st.sidebar.expander("Explore Characters", expanded=is_active_story):
        for char_obj in story_data["characters"]:
            char_b64 = get_image_base64(char_obj.get("avatar", ""))
            char_thumb = f'<img class="char-pill-avatar" src="{char_b64}">' if char_b64 else '<div class="char-pill-fallback">👤</div>'
            
            col_thumb, col_btn = st.columns([1, 4])
            with col_thumb:
                st.markdown(char_thumb, unsafe_allow_html=True)
            with col_btn:
                is_selected = (char_obj["name"] == st.session_state.selected_char and is_active_story)
                label = f"✨ {char_obj['name']}" if is_selected else char_obj["name"]
                if st.button(label, key=f"btn_{story_name}_{char_obj['name']}", use_container_width=True):
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
avatar_portrait_html = f'<img class="profile-portrait" src="{avatar_b64}">' if avatar_b64 else '<div class="profile-portrait-fallback">📖</div>'
st.sidebar.markdown(f"""
<div class="profile-card">
    {avatar_portrait_html}
    <div class="profile-name">{current_char['name']}</div>
    <div class="profile-source">{selected_story}</div>
    <div class="profile-tagline">
        {current_char.get('tagline', '')}
    </div>
</div>
""", unsafe_allow_html=True)

st.sidebar.write("")
if st.sidebar.button("🗑️ Reset Conversation", use_container_width=True):
    now = get_hkt_time()
    st.session_state.character_chats[current_char["name"]] = [
        {"role": "assistant", "content": f"Hello! I am {current_char['name']}. What would you like to explore together?", "time": now}
    ]
    st.session_state.failed_prompts.pop(current_char["name"], None)
    st.rerun()

# 9. Session Message History
now_str = get_hkt_time()
if current_char["name"] not in st.session_state.character_chats:
    st.session_state.character_chats[current_char["name"]] = [
        {
            "role": "assistant",
            "content": f"Hello! I am {current_char['name']}. What would you like to explore together?",
            "time": now_str
        }
    ]

# Purge any empty messages
st.session_state.character_chats[current_char["name"]] = [
    m for m in st.session_state.character_chats[current_char["name"]] 
    if m.get("content", "").strip() != ""
]
current_messages = st.session_state.character_chats[current_char["name"]]

# 10. Floating Frosted Hero Header
avatar_header_html = f'<img class="hero-avatar" src="{avatar_b64}">' if avatar_b64 else '<div class="hero-avatar-fallback">📖</div>'
st.markdown(f"""
<div class="hero-header">
    {avatar_header_html}
    <div class="hero-info">
        <h3>{current_char['name']}</h3>
        <div class="hero-badge-row">
            <span class="hero-tag">{selected_story}</span>
            <span class="live-indicator"><span class="pulse-dot"></span> Ready</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# 11. Modern Starter Prompts
starters = current_char.get("starter_questions", [])
if len(current_messages) <= 1 and starters:
    st.caption("Prompt ideas:")
    cols = st.columns(len(starters))
    for idx, question in enumerate(starters):
        if cols[idx].button(question, key=f"{current_char['name']}_chip_{idx}", use_container_width=True):
            st.session_state.pending_prompt = question
            st.rerun()

# 12. Render Clean Editorial Chat Feed
for msg in current_messages:
    role = msg["role"]
    content = msg["content"]
    time_str = msg.get("time", now_str)
    
    st.markdown(
        f'<div class="msg-row {role}"><div class="msg-card {role}">{content}<span class="msg-time">{time_str}</span></div></div>',
        unsafe_allow_html=True
    )

# 13. Smart Retry Notification
if current_char["name"] in st.session_state.failed_prompts:
    failed_text = st.session_state.failed_prompts[current_char["name"]]
    st.warning(f"Connection timed out on: '{failed_text}'")
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("🔄 Try Again", key="retry_btn_action", use_container_width=True):
            st.session_state.pending_prompt = st.session_state.failed_prompts.pop(current_char["name"])
            st.rerun()
    with col2:
        if st.button("Dismiss", key="dismiss_btn_action", use_container_width=True):
            st.session_state.failed_prompts.pop(current_char["name"])
            st.rerun()

# 14. Input & Stream Handling
user_query = st.chat_input(f"Ask {current_char['name']} a question...")
if "pending_prompt" in st.session_state:
    user_query = st.session_state.pop("pending_prompt")

if user_query:
    if not api_key:
        st.error("Please configure OPENROUTER_API_KEY in Secrets.")
        st.stop()

    current_time = get_hkt_time()

    # Append student query
    st.session_state.character_chats[current_char["name"]].append({
        "role": "user",
        "content": user_query,
        "time": current_time
    })
    st.markdown(
        f'<div class="msg-row user"><div class="msg-card user">{user_query}<span class="msg-time">{current_time}</span></div></div>',
        unsafe_allow_html=True
    )

    # Compile prompt context
    conversation_payload = [
        {"role": "system", "content": current_char["system_prompt"]}
    ]
    for m in st.session_state.character_chats[current_char["name"]]:
        conversation_payload.append({"role": m["role"], "content": m["content"]})

    # High-tech animated typing dots
    typing_box = st.empty()
    typing_box.markdown(f'''
    <div class="typing-card">
        <span>{current_char["name"]} is pondering</span>
        <span class="dot"></span><span class="dot"></span><span class="dot"></span>
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
                    f'<div class="msg-row assistant"><div class="msg-card assistant">{response_text}<span class="msg-time">{current_time}</span></div></div>',
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
            raise Exception("No text was returned by the provider. Please try again.")

    except Exception as e:
        typing_box.empty()
        bubble_placeholder.empty()
        
        if st.session_state.character_chats[current_char["name"]] and st.session_state.character_chats[current_char["name"]][-1]["role"] == "user":
            st.session_state.character_chats[current_char["name"]].pop()
            
        st.session_state.failed_prompts[current_char["name"]] = user_query
        st.rerun()
