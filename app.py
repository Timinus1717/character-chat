import os
import json
import base64
from datetime import datetime
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

# 2. Helper to encode local images for web rendering
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

# 3. Modern WhatsApp Theme CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Segoe+UI:wght@400;500;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, Helvetica, Arial, sans-serif;
    }

    /* Main chat container background with subtle WhatsApp doodle texture */
    .stApp {
        background-color: #efeae2;
        background-image: radial-gradient(#d5cdbf 0.75px, transparent 0.75px), radial-gradient(#d5cdbf 0.75px, #efeae2 0.75px);
        background-size: 30px 30px;
        background-position: 0 0, 15px 15px;
    }

    /* Clean up default Streamlit padding */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 5rem !important;
        max-width: 760px !important;
    }

    /* Sticky WhatsApp Header */
    .wa-header {
        position: sticky;
        top: 0;
        z-index: 99;
        display: flex;
        align-items: center;
        background-color: #075e54;
        background: linear-gradient(135deg, #075e54 0%, #128c7e 100%);
        padding: 10px 18px;
        border-radius: 14px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        margin-bottom: 20px;
    }
    .wa-avatar {
        width: 48px;
        height: 48px;
        border-radius: 50%;
        object-fit: cover;
        margin-right: 14px;
        border: 2px solid rgba(255, 255, 255, 0.85);
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
    }
    .wa-avatar-fallback {
        width: 48px;
        height: 48px;
        border-radius: 50%;
        background-color: #25d366;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 24px;
        margin-right: 14px;
        color: white;
    }
    .wa-header-info {
        flex-grow: 1;
    }
    .wa-header-info h3 {
        margin: 0;
        color: #ffffff;
        font-size: 1.15rem;
        font-weight: 600;
        letter-spacing: 0.3px;
    }
    .wa-header-info .status {
        margin: 0;
        color: #dcf8c6;
        font-size: 0.82rem;
        display: flex;
        align-items: center;
        gap: 6px;
    }
    .online-dot {
        width: 8px;
        height: 8px;
        background-color: #25d366;
        border-radius: 50%;
        display: inline-block;
        box-shadow: 0 0 6px #25d366;
    }

    /* Custom Message Bubbles */
    .chat-row {
        display: flex;
        width: 100%;
        margin-bottom: 12px;
    }
    .chat-row.user {
        justify-content: flex-end;
    }
    .chat-row.assistant {
        justify-content: flex-start;
    }

    .bubble {
        position: relative;
        max-width: 78%;
        padding: 9px 14px 22px 14px;
        font-size: 0.95rem;
        line-height: 1.45;
        color: #111b21;
        box-shadow: 0 1px 2px rgba(11, 20, 26, 0.13);
        word-wrap: break-word;
    }
    .bubble.user {
        background-color: #d9fdd3;
        border-radius: 12px 0px 12px 12px;
    }
    .bubble.assistant {
        background-color: #ffffff;
        border-radius: 0px 12px 12px 12px;
    }

    /* Message timestamp */
    .bubble-time {
        position: absolute;
        bottom: 4px;
        right: 10px;
        font-size: 0.70rem;
        color: #667781;
    }
    .bubble.user .bubble-time {
        color: #53bdeb;
    }

    /* Typing Indicator */
    .typing-indicator {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        padding: 8px 14px;
        background: #ffffff;
        border-radius: 12px;
        margin-bottom: 10px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.1);
        font-style: italic;
        color: #667781;
        font-size: 0.88rem;
    }

    /* Starter Question Buttons (Pill Chips) */
    .stButton button {
        background-color: #ffffff !important;
        color: #075e54 !important;
        border: 1px solid #c2dbd5 !important;
        border-radius: 20px !important;
        font-size: 0.88rem !important;
        font-weight: 500 !important;
        padding: 6px 14px !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06) !important;
    }
    .stButton button:hover {
        background-color: #075e54 !important;
        color: #ffffff !important;
        border-color: #075e54 !important;
        transform: translateY(-1px);
        box-shadow: 0 3px 6px rgba(0,0,0,0.12) !important;
    }

    /* Sidebar customization */
    [data-testid="stSidebar"] {
        background-color: #f0f2f5;
        border-right: 1px solid #d1d7db;
    }
    [data-testid="stSidebar"] h3 {
        color: #111b21;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# 4. OpenRouter API Connection
api_key = st.secrets.get("OPENROUTER_API_KEY", "")
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key or "missing_key"
)

MODEL_NAME = "openrouter/free"

# 5. Load Catalog directly (no cache so GitHub updates show immediately)
def load_catalog():
    with open(os.path.join(BASE_DIR, "characters.json"), "r", encoding="utf-8") as f:
        return json.load(f)

catalog = load_catalog()

# 6. Persistent Session Initialization
if "character_chats" not in st.session_state:
    st.session_state.character_chats = {}

# 7. Sidebar Navigation (Contact List)
st.sidebar.markdown("### 💬 Chats")
selected_story = st.sidebar.selectbox("Book / Story:", list(catalog.keys()))

character_list = catalog[selected_story]
char_dict = {c["name"]: c for c in character_list}

selected_char_name = st.sidebar.radio(
    "Select Contact:",
    options=list(char_dict.keys())
)

current_char = char_dict[selected_char_name]
avatar_b64 = get_image_base64(current_char.get("avatar", ""))

st.sidebar.divider()
if avatar_b64:
    st.sidebar.image(os.path.join(BASE_DIR, current_char["avatar"]), width=120)
st.sidebar.markdown(f"**About:** {current_char.get('tagline', '')}")

if st.sidebar.button("🗑️ Reset Chat", use_container_width=True):
    now = datetime.now().strftime("%I:%M %p")
    st.session_state.character_chats[selected_char_name] = [
        {"role": "assistant", "content": f"Hello! I am {selected_char_name}. What would you like to ask me?", "time": now}
    ]
    st.rerun()

# 8. Initialize chat for selected character if empty
now_str = datetime.now().strftime("%I:%M %p")
if selected_char_name not in st.session_state.character_chats:
    st.session_state.character_chats[selected_char_name] = [
        {
            "role": "assistant",
            "content": f"Hello! I am {current_char['name']}. What would you like to ask me?",
            "time": now_str
        }
    ]

current_messages = st.session_state.character_chats[selected_char_name]

# 9. Top WhatsApp Header
avatar_html = f'<img class="wa-avatar" src="{avatar_b64}">' if avatar_b64 else f'<div class="wa-avatar-fallback">📖</div>'
st.markdown(f"""
<div class="wa-header">
    {avatar_html}
    <div class="wa-header-info">
        <h3>{current_char['name']}</h3>
        <div class="status"><span class="online-dot"></span> online • {selected_story}</div>
    </div>
</div>
""", unsafe_allow_html=True)

# 10. Suggested Questions (Styled as clean pill chips)
starters = current_char.get("starter_questions", [])
if len(current_messages) <= 1 and starters:
    st.caption("Tap a question to ask:")
    cols = st.columns(len(starters))
    for idx, question in enumerate(starters):
        if cols[idx].button(question, key=f"{selected_char_name}_starter_{idx}", use_container_width=True):
            st.session_state.pending_prompt = question
            st.rerun()

# 11. Render Message Feed (WhatsApp Bubbles)
for msg in current_messages:
    role = msg["role"]
    content = msg["content"]
    time_str = msg.get("time", now_str)
    
    st.markdown(f"""
    <div class="chat-row {role}">
        <div class="bubble {role}">
            {content}
            <span class="bubble-time">{time_str}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

# 12. Handle Input & "is typing..."
user_query = st.chat_input(f"Type a message to {current_char['name']}...")
if "pending_prompt" in st.session_state:
    user_query = st.session_state.pop("pending_prompt")

if user_query:
    if not api_key:
        st.error("Please add OPENROUTER_API_KEY in Streamlit Secrets.")
        st.stop()

    current_time = datetime.now().strftime("%I:%M %p")

    # Save and display user bubble immediately
    st.session_state.character_chats[selected_char_name].append({
        "role": "user",
        "content": user_query,
        "time": current_time
    })
    st.markdown(f"""
    <div class="chat-row user">
        <div class="bubble user">
            {user_query}
            <span class="bubble-time">{current_time}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Prepare system payload
    conversation_payload = [
        {"role": "system", "content": current_char["system_prompt"]}
    ]
    for m in st.session_state.character_chats[selected_char_name]:
        conversation_payload.append({"role": m["role"], "content": m["content"]})

    # Render typing indicator
    typing_box = st.empty()
    typing_box.markdown(f"""
    <div class="typing-indicator">
        <span>✍️ <b>{current_char['name']}</b> is typing...</span>
    </div>
    """, unsafe_allow_html=True)

    try:
        stream = client.chat.completions.create(
            model=MODEL_NAME,
            messages=conversation_payload,
            stream=True,
            temperature=0.7,
            max_tokens=250
        )
        
        # Stream response directly into the assistant's bubble
        response_text = ""
        bubble_placeholder = st.empty()
        typing_box.empty()

        for chunk in stream:
            content = chunk.choices[0].delta.content or ""
            response_text += content
            bubble_placeholder.markdown(f"""
            <div class="chat-row assistant">
                <div class="bubble assistant">
                    {response_text}
                    <span class="bubble-time">{current_time}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # Save assistant message to session memory
        st.session_state.character_chats[selected_char_name].append({
            "role": "assistant",
            "content": response_text,
            "time": current_time
        })

    except Exception as e:
        typing_box.empty()
        st.error(f"API Error: {e}")
