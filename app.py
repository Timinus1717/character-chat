import json
import streamlit as st
from openai import OpenAI

st.set_page_config(
    page_title="Story Chat",
    page_icon="📖",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# 1. Connect to OpenRouter (Free-tier routing)
api_key = st.secrets.get("OPENROUTER_API_KEY", "")
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key or "missing_key"
)

# High-performing, permanently free model on OpenRouter
MODEL_NAME = "meta-llama/llama-3.2-3b-instruct:free"

# 2. Load Book & Character Catalog
@st.cache_data
def load_catalog():
    with open("characters.json", "r", encoding="utf-8") as f:
        return json.load(f)

catalog = load_catalog()

# 3. Sidebar Navigation
st.sidebar.title("📚 Select Character")
selected_story = st.sidebar.selectbox("Story:", list(catalog.keys()))
character_list = catalog[selected_story]
char_names = [c["name"] for c in character_list]
selected_char_name = st.sidebar.selectbox("Character:", char_names)

current_char = next(c for c in character_list if c["name"] == selected_char_name)

st.sidebar.markdown(f"**Bio:** {current_char.get('tagline', '')}")
if st.sidebar.button("🔄 Clear Chat", use_container_width=True):
    st.session_state.messages = []
    st.rerun()

# 4. Session State Setup
if "active_char" not in st.session_state or st.session_state.active_char != current_char["name"]:
    st.session_state.active_char = current_char["name"]
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": f"Greetings! I am {current_char['name']}. What would you like to ask me?"
        }
    ]

# 5. Header Display
st.markdown(f"### {current_char['avatar']} {current_char['name']}")
st.caption(f"From *{selected_story}*")

# 6. Starter Prompt Buttons
starters = current_char.get("starter_questions", [])
if len(st.session_state.messages) <= 1 and starters:
    st.write("**Suggested Questions:**")
    for idx, question in enumerate(starters):
        if st.button(question, key=f"starter_{idx}", use_container_width=True):
            st.session_state.pending_prompt = question
            st.rerun()

# 7. Message Feed
for msg in st.session_state.messages:
    avatar = current_char["avatar"] if msg["role"] == "assistant" else None
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])

# 8. User Input Handling
user_query = st.chat_input(f"Message {current_char['name']}...")
if "pending_prompt" in st.session_state:
    user_query = st.session_state.pop("pending_prompt")

if user_query:
    if not api_key:
        st.error("Please add OPENROUTER_API_KEY in your Streamlit app secrets.")
        st.stop()

    st.session_state.messages.append({"role": "user", "content": user_query})
    with st.chat_message("user"):
        st.markdown(user_query)

    conversation_payload = [
        {"role": "system", "content": current_char["system_prompt"]}
    ]
    for m in st.session_state.messages:
        conversation_payload.append({"role": m["role"], "content": m["content"]})

    with st.chat_message("assistant", avatar=current_char["avatar"]):
        try:
            stream = client.chat.completions.create(
                model=MODEL_NAME,
                messages=conversation_payload,
                stream=True,
                temperature=0.7,
                max_tokens=250
            )
            response_text = st.write_stream(stream)
            st.session_state.messages.append({"role": "assistant", "content": response_text})
        except Exception as e:
            st.error(f"API Error: {e}")
