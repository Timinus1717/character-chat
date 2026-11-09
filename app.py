import os
import json
import streamlit as st
from openai import OpenAI

# 1. Page Configuration
st.set_page_config(
    page_title="Story Chat",
    page_icon="💬",
    layout="centered",
    initial_sidebar_state="expanded"
)

# 2. WhatsApp-Style Clean CSS Styling
st.markdown("""
<style>
    /* Main background tint */
    .stApp {
        background-color: #ECE5DD;
    }
    
    /* Sticky Top Header bar resembling WhatsApp */
    .chat-header {
        display: flex;
        align-items: center;
        background-color: #075E54;
        color: white;
        padding: 10px 16px;
        border-radius: 10px;
        margin-bottom: 15px;
    }
    .chat-header img {
        width: 46px;
        height: 46px;
        border-radius: 50%;
        object-fit: cover;
        margin-right: 12px;
        border: 2px solid #ffffff;
    }
    .chat-header-info h3 {
        margin: 0;
        color: #ffffff;
        font-size: 1.15rem;
    }
    .chat-header-info p {
        margin: 0;
        color: #dcf8c6;
        font-size: 0.85rem;
    }
    
    /* Typing indicator styling */
    .typing-box {
        font-style: italic;
        color: #667781;
        font-size: 0.9rem;
        margin: 6px 0 10px 12px;
    }
    
    /* WhatsApp bubble aesthetics */
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

# 3. Connect to API
api_key = st.secrets.get("OPENROUTER_API_KEY", "")
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key or "missing_key"
)

# OpenRouter Free Router
MODEL_NAME = "openrouter/free"

# 4. Load Catalog
@st.cache_data
def load_catalog():
    with open("characters.json", "r", encoding="utf-8") as f:
        return json.load(f)

catalog = load_catalog()

# 5. Helper function for avatars
def resolve_avatar(avatar_path):
    """Returns local image path if valid, or a generic fallback."""
    if avatar_path and os.path.exists(avatar_path):
        return avatar_path
    return "📖"

# 6. Sidebar Navigation (WhatsApp contact list style)
st.sidebar.markdown("### 📚 Contacts")
selected_story = st.sidebar.selectbox("Select Story:", list(catalog.keys()))

character_list = catalog[selected_story]
char_dict = {c["name"]: c for c in character_list}

# Character selector with custom profile images
selected_char_name = st.sidebar.radio(
    "Select Character to Chat:",
    options=list(char_dict.keys()),
    format_func=lambda name: f"{name}"
)

current_char = char_dict[selected_char_name]
avatar_image = resolve_avatar(current_char.get("avatar", ""))

# Show character bio & preview in sidebar
st.sidebar.divider()
if os.path.exists(current_char.get("avatar", "")):
    st.sidebar.image(current_char["avatar"], width=100)
st.sidebar.markdown(f"**Bio:** {current_char.get('tagline', '')}")

if st.sidebar.button("🗑️ Clear This Chat", use_container_width=True):
    st.session_state.character_chats[selected_char_name] = [
        {"role": "assistant", "content": f"Hello! I am {selected_char_name}. What would you like to ask me?"}
    ]
    st.rerun()

# 7. Multi-Character Session Memory Initialization
if "character_chats" not in st.session_state:
    st.session_state.character_chats = {}

# Ensure selected character has their own conversation history
if selected_char_name not in st.session_state.character_chats:
    st.session_state.character_chats[selected_char_name] = [
        {
            "role": "assistant",
            "content": f"Hello! I am {current_char['name']}. What would you like to ask me?"
        }
    ]

# 8. WhatsApp-Style Header
header_img_tag = f'<img src="{current_char["avatar"]}">' if os.path.exists(current_char.get("avatar", "")) else '<span style="font-size:32px;margin-right:10px;">📖</span>'
st.markdown(f"""
<div class="chat-header">
    {header_img_tag}
    <div class="chat-header-info">
        <h3>{current_char['name']}</h3>
        <p>online • {selected_story}</p>
    </div>
</div>
""", unsafe_allow_html=True)

# 9. Starter Question Buttons (Only show if new conversation)
current_messages = st.session_state.character_chats[selected_char_name]
starters = current_char.get("starter_questions", [])

if len(current_messages) <= 1 and starters:
    st.caption("Suggested Questions:")
    for idx, question in enumerate(starters):
        if st.button(question, key=f"{selected_char_name}_starter_{idx}", use_container_width=True):
            st.session_state.pending_prompt = question
            st.rerun()

# 10. Display Messages for Current Character
for msg in current_messages:
    role = msg["role"]
    avatar = avatar_image if role == "assistant" else None
    with st.chat_message(role, avatar=avatar):
        st.markdown(msg["content"])

# 11. Handle Input & "Character is typing..." Indicator
user_query = st.chat_input(f"Message {current_char['name']}...")
if "pending_prompt" in st.session_state:
    user_query = st.session_state.pop("pending_prompt")

if user_query:
    if not api_key:
        st.error("Please add OPENROUTER_API_KEY in Streamlit Secrets.")
        st.stop()

    # Append to this character's persistent session history
    st.session_state.character_chats[selected_char_name].append({"role": "user", "content": user_query})
    with st.chat_message("user"):
        st.markdown(user_query)

    # Build prompt payload
    conversation_payload = [
        {"role": "system", "content": current_char["system_prompt"]}
    ]
    for m in st.session_state.character_chats[selected_char_name]:
        conversation_payload.append({"role": m["role"], "content": m["content"]})

    # Render assistant response with dynamic typing placeholder
    with st.chat_message("assistant", avatar=avatar_image):
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
            # Remove typing indicator before writing the streaming output
            typing_placeholder.empty()
            response_text = st.write_stream(stream)
            
            # Save assistant reply to memory
            st.session_state.character_chats[selected_char_name].append({"role": "assistant", "content": response_text})
        except Exception as e:
            typing_placeholder.empty()
            st.error(f"API Error: {e}")
