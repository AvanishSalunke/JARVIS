import json
import os
import uuid
from datetime import datetime

# CONFIGURATION
DATA_DIR = "data"
USERS_DIR = os.path.join(DATA_DIR, "users")

os.makedirs(USERS_DIR, exist_ok=True)

# INTERNAL HELPERS
def _sanitize_user_id(user_id: str) -> str:
    """Prevent path traversal & invalid folder names"""
    return "".join(c for c in user_id if c.isalnum() or c in ("-", "_"))

def _get_user_dir(user_id: str) -> str:
    safe_id = _sanitize_user_id(user_id)
    user_dir = os.path.join(USERS_DIR, safe_id)
    os.makedirs(user_dir, exist_ok=True)
    return user_dir

def _get_chats_path(user_id: str) -> str:
    return os.path.join(_get_user_dir(user_id), "chats.json")

def _get_memory_path(user_id: str) -> str:
    return os.path.join(_get_user_dir(user_id), "memory.json")

def _ensure_user_files(user_id: str):
    chats_path = _get_chats_path(user_id)
    memory_path = _get_memory_path(user_id)

    if not os.path.exists(chats_path):
        with open(chats_path, "w", encoding="utf-8") as f:
            json.dump({}, f)

    if not os.path.exists(memory_path):
        with open(memory_path, "w", encoding="utf-8") as f:
            json.dump([], f)

# PUBLIC INIT
def init_db(user_id: str):
    """Initialize per-user storage"""
    _ensure_user_files(user_id)

# CHAT FUNCTIONS
def get_all_chats(user_id: str):
    """Returns chat list for sidebar"""
    _ensure_user_files(user_id)

    with open(_get_chats_path(user_id), "r", encoding="utf-8") as f:
        data = json.load(f)

    chats = []
    for chat_id, chat in data.items():
        chats.append({
            "chat_id": chat_id,
            "name": chat.get("title", "New Conversation"),
            "timestamp": chat.get("created_at", "")
        })

    chats.sort(key=lambda x: x["timestamp"], reverse=True)
    return chats

def create_new_chat(user_id: str):
    """Create new chat scoped to user"""
    _ensure_user_files(user_id)

    chat_id = uuid.uuid4().hex
    now = datetime.utcnow().isoformat()

    new_chat = {
        "title": "New Conversation",
        "created_at": now,
        "messages": []
    }

    path = _get_chats_path(user_id)
    with open(path, "r+", encoding="utf-8") as f:
        data = json.load(f)
        data[chat_id] = new_chat
        f.seek(0)
        json.dump(data, f, indent=4)
        f.truncate()

    return {"chat_id": chat_id, "name": new_chat["title"]}

def rename_chat(chat_id: str, new_name: str, user_id: str):
    _ensure_user_files(user_id)
    path = _get_chats_path(user_id)

    with open(path, "r+", encoding="utf-8") as f:
        data = json.load(f)
        if chat_id not in data:
            return False

        data[chat_id]["title"] = new_name
        f.seek(0)
        json.dump(data, f, indent=4)
        f.truncate()

    return True

def delete_chat(chat_id: str, user_id: str):
    _ensure_user_files(user_id)
    path = _get_chats_path(user_id)

    with open(path, "r+", encoding="utf-8") as f:
        data = json.load(f)
        if chat_id not in data:
            return False

        del data[chat_id]
        f.seek(0)
        json.dump(data, f, indent=4)
        f.truncate()

    return True

def get_chat_history(chat_id: str, user_id: str):
    _ensure_user_files(user_id)

    with open(_get_chats_path(user_id), "r", encoding="utf-8") as f:
        data = json.load(f)

    return data.get(chat_id, {}).get("messages", [])

def append_to_chat(chat_id: str, role: str, content: str, user_id: str):
    _ensure_user_files(user_id)
    path = _get_chats_path(user_id)

    with open(path, "r+", encoding="utf-8") as f:
        data = json.load(f)
        if chat_id not in data:
            return

        data[chat_id]["messages"].append({
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat()
        })

        f.seek(0)
        json.dump(data, f, indent=4)
        f.truncate()

# LONG-TERM MEMORY
def get_long_term_memory(user_id: str):
    _ensure_user_files(user_id)

    with open(_get_memory_path(user_id), "r", encoding="utf-8") as f:
        return json.load(f)

def add_long_term_memory(memory_text: str, user_id: str):
    _ensure_user_files(user_id)
    path = _get_memory_path(user_id)

    with open(path, "r+", encoding="utf-8") as f:
        memories = json.load(f)
        if memory_text not in memories:
            memories.append(memory_text)
            f.seek(0)
            json.dump(memories, f, indent=4)
            f.truncate()
