import json
import os
import uuid
from datetime import datetime

DB_FILE = "chat_data.json"

def load_data():
    """Loads all chats and long-term memory from JSON."""
    if not os.path.exists(DB_FILE):
        # Default structure if file doesn't exist
        return {"chats": {}, "long_term_memory": []}
    try:
        with open(DB_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, ValueError):
        return {"chats": {}, "long_term_memory": []}

def save_data(data):
    """Saves the data back to JSON."""
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)

def create_new_chat():
    """Creates a new empty chat session."""
    data = load_data()
    chat_id = str(uuid.uuid4())
    chat_name = f"Chat {datetime.now().strftime('%m-%d %H:%M')}"
    
    data["chats"][chat_id] = {
        "name": chat_name,
        "history": []
    }
    save_data(data)
    return chat_id

def rename_chat(chat_id, new_name):
    """Renames a specific chat."""
    data = load_data()
    if chat_id in data["chats"]:
        data["chats"][chat_id]["name"] = new_name
        save_data(data)

def delete_chat(chat_id):
    """Deletes a chat."""
    data = load_data()
    if chat_id in data["chats"]:
        del data["chats"][chat_id]
        save_data(data)

def get_chat_history(chat_id):
    """Gets history for a specific chat."""
    data = load_data()
    return data["chats"].get(chat_id, {}).get("history", [])

def append_to_chat(chat_id, role, content):
    """Adds a message to a specific chat."""
    data = load_data()
    if chat_id in data["chats"]:
        data["chats"][chat_id]["history"].append({"role": role, "content": content})
        save_data(data)

def get_long_term_memory():
    """Gets the global facts."""
    data = load_data()
    return data.get("long_term_memory", [])

def add_long_term_memory(fact):
    """Adds a global fact usable by ALL chats."""
    data = load_data()
    if fact not in data["long_term_memory"]:
        data["long_term_memory"].append(fact)
        save_data(data)