import json
import os
import uuid
from datetime import datetime

# --- CONFIGURATION ---
DATA_DIR = "data"
USERS_DIR = os.path.join(DATA_DIR, "users")

# Ensure base data directory exists
os.makedirs(USERS_DIR, exist_ok=True)

# --- HELPER: GET PATHS ---
def _get_user_paths(user_id):
    """
    Generates paths for a specific user's data.
    Structure: data/users/{username}/chats.json
    """
    # Sanitize user_id to prevent path traversal issues
    safe_uid = "".join([c for c in user_id if c.isalnum() or c in ('-', '_')])
    user_folder = os.path.join(USERS_DIR, safe_uid)
    
    if not os.path.exists(user_folder):
        os.makedirs(user_folder)
        
    return {
        "chats": os.path.join(user_folder, "chats.json"),
        "memory": os.path.join(user_folder, "memory.json")
    }

# --- INITIALIZE FILES ---
def init_db(user_id):
    """Ensures the user's data files exist."""
    paths = _get_user_paths(user_id)
    
    if not os.path.exists(paths["chats"]):
        with open(paths["chats"], "w") as f:
            json.dump({}, f)
    
    if not os.path.exists(paths["memory"]):
        with open(paths["memory"], "w") as f:
            json.dump([], f)
    return paths

# --- CHAT FUNCTIONS ---

def get_all_chats(user_id):
    """Returns [{chat_id, name, timestamp}] for the sidebar."""
    paths = init_db(user_id)
    try:
        with open(paths["chats"], "r") as f:
            data = json.load(f)
        
        chat_list = []
        for chat_id, chat_data in data.items():
            chat_list.append({
                "chat_id": chat_id,
                "name": chat_data.get("title", "New Conversation"),
                "timestamp": chat_data.get("created_at", "")
            })
        
        # Sort by newest first
        chat_list.sort(key=lambda x: x["timestamp"], reverse=True)
        return chat_list
    except:
        return []

def create_new_chat(user_id):
    """Creates a new chat and returns {chat_id, name}."""
    paths = init_db(user_id)
    chat_id = uuid.uuid4().hex
    timestamp = datetime.now().isoformat()
    title = "New Conversation"
    
    new_chat = {
        "title": title,
        "created_at": timestamp,
        "messages": []
    }
    
    with open(paths["chats"], "r+") as f:
        data = json.load(f)
        data[chat_id] = new_chat
        f.seek(0)
        json.dump(data, f, indent=4)
        
    return {"chat_id": chat_id, "name": title}

def rename_chat(chat_id, new_name, user_id):
    """Renames a specific chat for a specific user."""
    paths = init_db(user_id)
    try:
        with open(paths["chats"], "r+") as f:
            data = json.load(f)
            if chat_id in data:
                data[chat_id]["title"] = new_name
                f.seek(0)
                json.dump(data, f, indent=4)
                f.truncate()
                return True
    except:
        pass
    return False

def delete_chat(chat_id, user_id):
    """Deletes a chat for a specific user."""
    paths = init_db(user_id)
    try:
        with open(paths["chats"], "r+") as f:
            data = json.load(f)
            if chat_id in data:
                del data[chat_id]
                f.seek(0)
                json.dump(data, f, indent=4)
                f.truncate()
                return True
    except:
        pass
    return False

def get_chat_history(chat_id, user_id):
    """Returns list of message dicts for a specific user/chat."""
    paths = init_db(user_id)
    try:
        with open(paths["chats"], "r") as f:
            data = json.load(f)
            return data.get(chat_id, {}).get("messages", [])
    except:
        return []

def append_to_chat(chat_id, role, content, user_id):
    """Saves a message to the user's JSON file."""
    paths = init_db(user_id)
    try:
        with open(paths["chats"], "r+") as f:
            data = json.load(f)
            if chat_id in data:
                data[chat_id]["messages"].append({"role": role, "content": content})
                f.seek(0)
                json.dump(data, f, indent=4)
    except:
        pass

# --- MEMORY FUNCTIONS (User Specific) ---

def get_long_term_memory(user_id):
    """Returns list of memory strings for a specific user."""
    paths = init_db(user_id)
    try:
        with open(paths["memory"], "r") as f:
            return json.load(f)
    except:
        return []

def add_long_term_memory(memory_text, user_id):
    """Adds a new string to the user's memory.json."""
    paths = init_db(user_id)
    try:
        with open(paths["memory"], "r+") as f:
            memories = json.load(f)
            if memory_text not in memories:
                memories.append(memory_text)
                f.seek(0)
                json.dump(memories, f, indent=4)
    except:
        pass