import streamlit as st
import memory_manager as mem
import llm_services as brain
from langchain_core.messages import HumanMessage, AIMessage

DEFAULT_USER_ID = "streamlit_user"

# Page Config
st.set_page_config(page_title="Jarvis AI", layout="wide")

# CSS for Sidebar
st.markdown("""
<style>
    section[data-testid="stSidebar"] { overflow-y: auto; }
    .stButton button { width: 100%; text-align: left; }
</style>
""", unsafe_allow_html=True)

# Session State Init
if "current_chat_id" not in st.session_state:
    data = mem.load_data()
    if not data["chats"]:
        st.session_state["current_chat_id"] = mem.create_new_chat()
    else:
        # Load the most recent chat
        st.session_state["current_chat_id"] = list(data["chats"].keys())[-1]

# SIDEBAR
with st.sidebar:
    st.title("🗂️ Jarvis Memory")
    
    if st.button("+ New Chat", type="primary"):
        new_id = mem.create_new_chat()
        st.session_state["current_chat_id"] = new_id
        st.rerun()

    st.markdown("---")

    data = mem.load_data()
    # Show newest first
    chat_ids = list(data["chats"].keys())[::-1] 
    
    for chat_id in chat_ids:
        chat_name = data["chats"][chat_id]["name"]
        
        col1, col2 = st.columns([0.85, 0.15])
        with col1:
            is_active = (chat_id == st.session_state["current_chat_id"])
            if st.button(f"{'🟢 ' if is_active else ''}{chat_name}", key=chat_id):
                st.session_state["current_chat_id"] = chat_id
                st.rerun()
        with col2:
            if st.button("✕", key=f"del_{chat_id}"):
                mem.delete_chat(chat_id)
                if chat_id == st.session_state["current_chat_id"]:
                    st.session_state["current_chat_id"] = mem.create_new_chat()
                st.rerun()

    st.markdown("---")
    
    if st.session_state["current_chat_id"] in data["chats"]:
        curr_id = st.session_state["current_chat_id"]
        curr_name = data["chats"][curr_id]["name"]
        new_name = st.text_input("Rename Chat", value=curr_name)
        if new_name != curr_name:
            mem.rename_chat(curr_id, new_name)
            st.rerun()

# MAIN AREA 
current_id = st.session_state["current_chat_id"]
# Reload data to ensure we have the latest updates from Backend API if any
data = mem.load_data()
chat_data = data["chats"].get(current_id, {"name": "New Chat", "history": []})
history = chat_data["history"]
long_term_mem = mem.get_long_term_memory(user_id=DEFAULT_USER_ID)

st.header(f"💬 {chat_data['name']}")

# Display History
for msg in history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# User Input
if user_input := st.chat_input("Talk to Jarvis..."):
    with st.chat_message("human"):
        st.markdown(user_input)
    
    mem.append_to_chat(current_id, "human", user_input)

    # Convert to LangChain objects
    langchain_history = []
    for h in history:
        if h["role"] == "human":
            langchain_history.append(HumanMessage(content=h["content"]))
        else:
            langchain_history.append(AIMessage(content=h["content"]))

    # Get Response
    with st.spinner("Thinking..."):
        ai_response = brain.get_brain_response(user_input, langchain_history, long_term_mem)

    with st.chat_message("ai"):
        st.markdown(ai_response)

    mem.append_to_chat(current_id, "ai", ai_response)