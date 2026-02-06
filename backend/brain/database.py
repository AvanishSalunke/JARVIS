import json
import os
import uuid
from datetime import datetime
from . import memory_manager

# --- CONFIGURATION ---
CHATS_FILE = "data/chats.json"

# Ensure data directory exists
os.makedirs("data", exist_ok=True)

# --- INITIALIZE FILES ---
def init_db():
    if not os.path.exists(CHATS_FILE):
        with open(CHATS_FILE, "w") as f:
            json.dump({}, f)

# --- CHAT MANAGEMENT ---
def get_all_chats():
    """Returns a list of all chat sessions with their IDs and Titles."""
    init_db()
    try:
        with open(CHATS_FILE, "r") as f:
            data = json.load(f)
            # Return list of {id, title, timestamp}
            chat_list = []
            for chat_id, chat_data in data.items():
                chat_list.append({
                    "id": chat_id,
                    "title": chat_data.get("title", "New Conversation"),
                    "created_at": chat_data.get("created_at", "")
                })
            # Sort by newest first (optional)
            return chat_list
    except:
        return []

def get_chat_history(chat_id):
    init_db()
    with open(CHATS_FILE, "r") as f:
        data = json.load(f)
        return data.get(chat_id, {}).get("messages", [])

def create_chat(title="New Conversation"):
    init_db()
    chat_id = str(uuid.uuid4().hex)
    new_chat = {
        "title": title,
        "created_at": str(datetime.now()),
        "messages": []
    }
    
    with open(CHATS_FILE, "r+") as f:
        data = json.load(f)
        data[chat_id] = new_chat
        f.seek(0)
        json.dump(data, f, indent=4)
        
    return chat_id

def save_message(chat_id, role, content):
    """Saves a single message to a specific chat."""
    init_db()
    with open(CHATS_FILE, "r+") as f:
        data = json.load(f)
        
        if chat_id not in data:
            # If chat doesn't exist, create it locally in memory first
            data[chat_id] = {
                "title": "New Conversation", 
                "created_at": str(datetime.now()), 
                "messages": []
            }
            
        data[chat_id]["messages"].append({"role": role, "content": content})
        
        f.seek(0)
        json.dump(data, f, indent=4)

def rename_chat(chat_id, new_title):
    """Renames a specific chat."""
    init_db()
    with open(CHATS_FILE, "r+") as f:
        data = json.load(f)
        if chat_id in data:
            data[chat_id]["title"] = new_title
            f.seek(0)
            json.dump(data, f, indent=4)
            return True
        return False

# --- LONG TERM MEMORY ---
def get_long_term_memory(user_id: str):
    """Returns the list of core memories for a specific user."""
    return memory_manager.get_long_term_memory(user_id)

def add_long_term_memory(memory_text: str, user_id: str):
    """Adds a new fact to long term memory for a specific user."""
    memory_manager.add_long_term_memory(memory_text, user_id)