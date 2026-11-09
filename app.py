import os
import json
import base64
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
    """Encodes local images to Base64 so Streamlit and HTML can render them reliably."""
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

# 3. WhatsApp-Style Clean CSS Styling
st.markdown("""
<style>
    /* WhatsApp conversation background */
    .stApp {
        background-color: #ECE5DD;
    }
    
    /* WhatsApp contact banner header */
    .chat-header {
        display: flex;
        align-items: center;
        background-color: #075E54;
        color: white;
        padding: 10px 16px;
        border-radius: 12px;
        margin-bottom: 15px;
    }
    .chat-header img {
        width: 48px;
        height: 48px;
        border-radius: 50%;
        object-fit: cover;
        margin-right: 14px;
        border: 2px solid #ffffff;
    }
    .chat-header-info h3 {
        margin: 0;
        color: #ffffff;
        font-size: 1.15rem;
        font-weight: 600;
    }
    .chat-header-info p {
        margin: 0;
        color: #dcf8c6;
        font-size: 0.85rem;
    }
    
    /* WhatsApp message bubble styling */
    [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {
        background-color: #DCF8C6 !important;
        border-radius: 12px 0 12px 12px !important;
        margin-left: auto !important;
        width: fit-content !important;
        max-width: 80% !important;
        box-shadow: 0 1px 1px rgba(0,0,0,0.1);
    }
    [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) {
        background-color: #FFFFFF !important;
        border-radius: 0 12px 12px 12px !important;
        margin-right: auto !important;
        width: fit-content !important;
        max-width: 80% !important;
        box-shadow: 0 1px 1px rgba(0,0,0,0.1);
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

# 5. Load Book & Character Catalog
@st.cache_data
def load_catalog():
    with open(os.path.join(BASE_DIR, "characters.json"), "r", encoding="utf-8") as f:
        return json.load(f)

catalog = load_catalog()

# 6. Multi-Character Persistent Session Setup
if "character_chats" not in st.session_state:
    st.session_state.character_chats = {}

# 7. Sidebar Navigation (Contact List)
st.sidebar.markdown("### 📚 Contacts")
selected_story = st.sidebar.selectbox("Select Story:", list(catalog.keys()))

character_list = catalog[selected_story]
char_dict = {c["name"]: c for c in character_list}

selected_char_name = st.sidebar.radio(
    "Choose Character:",
    options=list(char_dict.keys())
)

current_char = char_dict[selected_char_name]

# Resolve profile image (Base64 Data URI)
avatar_b64 = get_image_base64(current_char.get("avatar", ""))
chat_avatar = avatar_b64 if avatar_b64 else "📖"

# Show profile preview & bio in sidebar
st.sidebar.divider()
if avatar_b64:
    st.sidebar.image(os.path.join(BASE_DIR, current_char["avatar"]), width=120)
st.sidebar.markdown(f"**Bio:** {current_char.get('tagline', '')}")

if st.sidebar.button("🗑️ Clear This Chat", use_container_width=True):
    st.session_state.character_chats[selected_char_name] = [
        {"role": "assistant", "content": f"Hello! I am {selected_char_name}. What would you like to ask me?"}
    ]
    st.rerun()

# Initialize selected character's chat history if not yet created
if selected_char_name not in st.session_state.character_chats:
    st.session_state.character_chats[selected_char_name] = [
        {
            "role": "assistant",
            "content": f"Hello! I am {current_char['name']}. What would you like to ask me?"
        }
    ]

current_messages = st.session_state.character_chats[selected_char_name]

# 8. WhatsApp-Style Header Banner
header_img_tag = f'<img src="{avatar_b64}">' if avatar_b64 else '<span style="font-size:32px;margin-right:12px;">📖</span>'
st.markdown(f"""
<div class="chat-header">
    {header_img_tag}
    <div class="chat-header-info">
        <h3>{current_char['name']}</h3>
        <p>online • {selected_story}</p>
    </div>
</div>
""", unsafe_allow_html=True)

# 9. Starter Question Buttons (Only displays on a fresh conversation)
starters = current_char.get("starter_questions", [])
if len(current_messages) <= 1 and starters:
    st.caption("Suggested Questions:")
    for idx, question in enumerate(starters):
        if st.button(question, key=f"{selected_char_name}_starter_{idx}", use_container_width=True):
            st.session_state.pending_prompt = question
            st.rerun()

# 10. Render Conversation History for Current Character
for msg in current_messages:
    role = msg["role"]
    avatar = chat_avatar if role == "assistant" else None
    with st.chat_message(role, avatar=avatar):
        st.markdown(msg["content"])

# 11. Handle Chat Input & "is typing..." Indicator
user_query = st.chat_input(f"Message {current_char['name']}...")
if "pending_prompt" in st.session_state:
    user_query = st.session_state.pop("pending_prompt")

if user_query:
    if not api_key:
        st.error("Please add OPENROUTER_API_KEY in Streamlit Secrets.")
        st.stop()

    # Save student message to memory
    st.session_state.character_chats[selected_char_name].append({"role": "user", "content": user_query})
    with st.chat_message("user"):
        st.markdown(user_query)

    # Build prompt payload
    conversation_payload = [
        {"role": "system", "content": current_char["system_prompt"]}
    ]
    for m in st.session_state.character_chats[selected_char_name]:
        conversation_payload.append({"role": m["role"], "content": m["content"]})

    # Render character response with typing placeholder
    with st.chat_message("assistant", avatar=chat_avatar):
        typing_placeholder = st.empty()
        typing_placeholder.markdown(f"*{current_char['name']} is typing...*")

        try:
            stream = client.chat.completions.create(
                model=MODEL_NAME,
                messages=conversation_payload,
                stream=True,
                temperature=0.7,
                max_tokens=250
            )
            typing_placeholder.empty()
            response_text = st.write_stream(stream)
            
            # Save assistant reply to memory
            st.session_state.character_chats[selected_char_name].append({"role": "assistant", "content": response_text})
        except Exception as e:
            typing_placeholder.empty()
            st.error(f"API Error: {e}")
