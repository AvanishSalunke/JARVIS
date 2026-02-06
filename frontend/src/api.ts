/* src/api.ts */

const API_BASE = "http://127.0.0.1:8000";

export interface ChatItem {
  chat_id: string;
  name: string;
}

export interface ChatMessage {
  role: "human" | "ai";
  content: string;
}

// --- AUTH HELPER ---
const getAuthHeaders = (): Record<string, string> => {
  const token = localStorage.getItem("jarvis_token");
  return token ? { "Authorization": `Bearer ${token}` } : {};
};

// --- MANAGEMENT ---

export const fetchChatList = async (): Promise<ChatItem[]> => {
  try {
    const res = await fetch(`${API_BASE}/chats`, {
      headers: { ...getAuthHeaders() }
    });
    if (res.status === 401) throw new Error("Unauthorized");
    return await res.json();
  } catch (e) {
    console.error("Failed to fetch chats:", e);
    return [];
  }
};

export const createNewChat = async (): Promise<ChatItem> => {
  const res = await fetch(`${API_BASE}/chats/new`, { 
    method: "POST",
    headers: { ...getAuthHeaders() }
  });
  return await res.json();
};

export const fetchChatHistory = async (chatId: string): Promise<ChatMessage[]> => {
  const res = await fetch(`${API_BASE}/chats/${chatId}/history`, {
    headers: { ...getAuthHeaders() }
  });
  return await res.json();
};

export const deleteChat = async (chatId: string) => {
  await fetch(`${API_BASE}/chats/${chatId}`, { 
    method: "DELETE",
    headers: { ...getAuthHeaders() }
  });
};

export const renameChat = async (chatId: string, newName: string) => {
  try {
    await fetch(`${API_BASE}/chats/${chatId}`, {
      method: "PUT",
      headers: { 
        "Content-Type": "application/json",
        ...getAuthHeaders()
      },
      body: JSON.stringify({ new_name: newName }),
    });
  } catch (error) {
    console.error("Error renaming chat:", error);
  }
};

// --- CORE INTERACTION ---

export const sendMessage = async (text: string, chatId: string | null) => {
  const res = await fetch(`${API_BASE}/chat`, {
    method: "POST",
    headers: { 
        "Content-Type": "application/json",
        ...getAuthHeaders()
    },
    body: JSON.stringify({ text, chatId: chatId }),
  });
  
  if (res.status === 401) {
    window.location.href = "/login"; // Force redirect if token expires
  }
  return await res.json();
};

// --- MULTIMEDIA (Vision/Voice) ---

export const sendImageQuestion = async (file: File, question: string, chatId: string | null) => {
    const form = new FormData();
    form.append("file", file);
    form.append("question", question);
    if (chatId) form.append("chat_id", chatId);

    // Note: Fetch handles Content-Type for FormData automatically, 
    // but we still need to append the Authorization header.
    const res = await fetch(`${API_BASE}/image_qa`, {
        method: "POST",
        headers: { ...getAuthHeaders() }, 
        body: form,
    });

    return await res.json();
};
export async function sendAudio(audio: Blob, chatId: string | null) {
  const formData = new FormData();
  formData.append("audio", audio);
  if (chatId) formData.append("chat_id", chatId);

  const res = await fetch("http://127.0.0.1:8000/audio", {
    method: "POST",
    body: formData,
  });

  return res.json();
}


export const playTTS = async (text: string) => {
  try {
    const res = await fetch(`${API_BASE}/tts`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
    });

    if (!res.ok) throw new Error("TTS Generation failed");

    const blob = await res.blob();
    const audioUrl = URL.createObjectURL(blob);
    const audio = new Audio(audioUrl);
    audio.play();
  } catch (e) {
    console.error("Audio Playback Error:", e);
  }
};