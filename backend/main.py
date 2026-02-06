import os
import sys
import warnings
import logging

# --- SILENCE WARNINGS (Updated) ---
# 1. Silence HuggingFace Hub (Fixes "unauthenticated requests" warning)
os.environ["HF_HUB_VERBOSITY"] = "error" 
os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"

# 2. Silence Transformers & TensorFlow
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3" 
os.environ["TRANSFORMERS_VERBOSITY"] = "error"

# 3. Force Python Logger to ignore HF warnings
logging.getLogger("huggingface_hub").setLevel(logging.ERROR)
logging.getLogger("transformers").setLevel(logging.ERROR)

# 4. Filter Deprecation Warnings (LangChain/Pydantic)
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)
# ------------------------

import sys
import pathlib
import json    
import asyncio
import os
import io
import uuid
import subprocess
import edge_tts 
import re
import shutil
from contextlib import asynccontextmanager

# Allow running this file directly from the `backend/` directory for convenience.
if __package__ is None:
    repo_root = pathlib.Path(__file__).resolve().parent.parent
    repo_root_str = str(repo_root)
    if repo_root_str not in sys.path:
        sys.path.insert(0, repo_root_str)

from fastapi import FastAPI, UploadFile, File, HTTPException, Body, Form, Depends, status, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, Field
from typing import Optional, List
from faster_whisper import WhisperModel

# =====================
# IMPORTS
# =====================
from backend.brain import memory_manager as mem
from backend.brain import llm_services as brain
from backend.brain import web_search as searcher     
from backend import auth 

from langchain_core.messages import HumanMessage, AIMessage

# =====================
# CONFIG & LIFESPAN
# =====================
FFMPEG_PATH = shutil.which("ffmpeg") or r"C:\ffmpeg\bin\ffmpeg.exe"
AGENT_PATH = os.path.join(os.path.dirname(__file__), "agent.exe")
connected_agent = None
agent_lock = asyncio.Lock()

# Global Model Variables
whisper_model = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- STARTUP LOGIC ---
    print("🚀 JARVIS Systems Initializing...")
    
    # 1. Start Local Agent
    try:
        if os.path.exists(AGENT_PATH):
            subprocess.Popen(AGENT_PATH)
            print("🚀 Local agent started automatically")
    except Exception as e:
        print("❌ Failed to start agent:", e)

    # 2. Load Whisper
    global whisper_model
    print("⏳ Loading Whisper Model...")
    whisper_model = WhisperModel("small.en", device="cpu", compute_type="int8")
    print("✅ Whisper Model Loaded!")

    # 3. Preload Multimodal
    print("⏳ Preloading Multimodal Model...")
    try:
        from backend.brain import local_multimodal
        if local_multimodal.is_available():
            local_multimodal._init_model()
            print("✅ Multimodal Model Preloaded!")
        else:
            print("⚠️ Multimodal Model not available")
    except Exception as e:
        print(f"⚠️ Failed to preload multimodal model: {e}")

    yield
    # --- SHUTDOWN LOGIC ---
    print("🛑 JARVIS Systems Shutting Down...")

# --- APP INITIALIZATION (DO THIS ONLY ONCE) ---
app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_methods=["*"],
    allow_headers=["*"],
)

# =====================
# REQUEST MODELS
# =====================
class ChatRequest(BaseModel):
    text: str
    chat_id: Optional[str] = Field(None, alias="chatId") 

class ChatResponse(BaseModel):
    response: str
    chat_id: str

class RenameRequest(BaseModel):
    new_name: str

class TTSRequest(BaseModel):
    text: str

class SignupRequest(BaseModel):
    username: str
    password: str

# =====================
# HELPER FUNCTIONS
# =====================

def extract_first_json(text):
    start = text.find("{")
    if start == -1:
        return None
    brace_count = 0
    for i in range(start, len(text)):
        if text[i] == "{":
            brace_count += 1
        elif text[i] == "}":
            brace_count -= 1
        if brace_count == 0:
            return text[start:i+1]
    return None 

def perform_search(query):
    print(f"🔎 Jarvis is searching the web for: {query}")
    tool = searcher.get_search_tool()
    try:
        result = tool.func(query)
        return str(result)[:2000] if len(str(result)) > 2000 else str(result)
    except Exception as e:
        print(f"❌ Search Error: {e}")
        return "I attempted to search but encountered an error."

# =====================
# 0. AUTH ENDPOINTS
# =====================

@app.post("/signup")
def signup(user: SignupRequest):
    """Register a new user."""
    # Check if user exists
    if auth.get_user(user.username):
        raise HTTPException(status_code=400, detail="Username already registered")
    
    auth.create_user_in_db(user.username, user.password)
    return {"status": "success", "message": "User created successfully"}

@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Standard OAuth2 login endpoint."""
    # FIXED: Was 'get_user_from_db', changed to 'get_user'
    user = auth.get_user(form_data.username)
    
    if not user or not auth.verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = auth.create_access_token(data={"sub": user["username"]})
    return {"access_token": access_token, "token_type": "bearer", "username": user["username"]}

# --- NEW: PROFILE ENDPOINT (Added for your requirement) ---
@app.get("/users/me")
def get_profile(current_user: str = Depends(auth.get_current_user)):
    """Returns the profile info for the logged-in user."""
    return {
        "username": current_user,
        "status": "online"
    }

# =====================
# 1. MANAGEMENT ENDPOINTS (PROTECTED)
# =====================

@app.get("/chats")
def list_chats(current_user: str = Depends(auth.get_current_user)):
    return mem.get_all_chats(user_id=current_user)

@app.post("/chats/new")
def create_chat(current_user: str = Depends(auth.get_current_user)):
    return mem.create_new_chat(user_id=current_user)

@app.put("/chats/{chat_id}")
def rename_chat(chat_id: str, req: RenameRequest, current_user: str = Depends(auth.get_current_user)):
    success = mem.rename_chat(chat_id, req.new_name, user_id=current_user)
    if not success:
        raise HTTPException(status_code=404, detail="Chat not found")
    return {"status": "success", "new_name": req.new_name}

@app.delete("/chats/{chat_id}")
def delete_chat(chat_id: str, current_user: str = Depends(auth.get_current_user)):
    success = mem.delete_chat(chat_id, user_id=current_user)
    if not success:
        raise HTTPException(status_code=404, detail="Chat not found")
    return {"status": "success"}

@app.get("/chats/{chat_id}/history")
def get_history(chat_id: str, current_user: str = Depends(auth.get_current_user)):
    return mem.get_chat_history(chat_id, user_id=current_user)

# =====================
# 2. CHAT & BRAIN ENDPOINT (PROTECTED)
# =====================

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest, current_user: str = Depends(auth.get_current_user)):
    user_text = req.text
    chat_id = req.chat_id

    # 1. Handle New Chat creation
    if not chat_id:
        new_chat = mem.create_new_chat(user_id=current_user)
        chat_id = new_chat["chat_id"]

    # 2. Get History
    history_dicts = mem.get_chat_history(chat_id, user_id=current_user)
    langchain_history = []
    for h in history_dicts:
        if h["role"] == "human":
            langchain_history.append(HumanMessage(content=h["content"]))
        else:
            langchain_history.append(AIMessage(content=h["content"]))

    # 3. Get LTM
    long_term_mem = mem.get_long_term_memory(user_id=current_user)

    # 4. FIRST CALL TO BRAIN
    ai_response = brain.get_brain_response(user_text, langchain_history, long_term_mem)
    ai_response = ai_response.replace("```json", "").replace("```", "")
    
    tool_data = None
    try:
        json_str = extract_first_json(ai_response)
        if json_str:
            tool_data = json.loads(json_str)
    except Exception as e:
        print("JSON parse fail:", e)

    # 5. AGENT HANDLING
    if isinstance(tool_data, dict) and "action" in tool_data:
        print("📤 Sending command to agent:", tool_data)

        if connected_agent:
            try:
                await connected_agent.send_text(json.dumps(tool_data))
                final_answer = f"Executing {tool_data['action']}..."
            except Exception as e:
                print("Agent send failed:", e)
                final_answer = "⚠️ Agent connected but command failed."
        else:
            final_answer = "⚠️ Local agent is not running."

        mem.append_to_chat(chat_id, "human", user_text, user_id=current_user)
        mem.append_to_chat(chat_id, "ai", final_answer, user_id=current_user)
        return ChatResponse(response=final_answer, chat_id=chat_id)

    # 6. WEB SEARCH HANDLING
    final_answer = ai_response
    try:
        if isinstance(tool_data, dict) and "query" in tool_data:
            search_query = tool_data["query"]
            search_results = perform_search(search_query)
            
            search_context = f"SYSTEM: I have searched Google. Here are the results: {search_results}\n\nUsing these results, answer the user's original question."
            
            langchain_history.append(HumanMessage(content=user_text))
            
            final_answer = brain.get_brain_response(search_context, langchain_history, long_term_mem)
    except Exception as e:
        print(f"⚠️ Tool call parsing failed, returning original response. Error: {e}")
        final_answer = ai_response

    # 7. Save to DB
    mem.append_to_chat(chat_id, "human", user_text, user_id=current_user)
    mem.append_to_chat(chat_id, "ai", final_answer, user_id=current_user)

    # 8. Auto-Save "My Name is"
    if "my name is" in user_text.lower():
        mem.add_long_term_memory(f"User Mentioned: {user_text}", user_id=current_user)

    return ChatResponse(response=final_answer, chat_id=chat_id)

# =====================
# 3. IMAGE QUESTION ENDPOINT (PROTECTED)
# =====================
@app.post("/image_qa", response_model=ChatResponse)
async def image_question(
    file: UploadFile = File(...), 
    question: str = Form(...), 
    chat_id: Optional[str] = Form(None),
    current_user: str = Depends(auth.get_current_user)
):
    if not chat_id:
        new_chat = mem.create_new_chat(user_id=current_user)
        chat_id = new_chat["chat_id"]

    contents = await file.read()

    # Step 1: Get the Image Description
    image_description = None
    error_message = None 
    
    try:
        from backend.brain import local_multimodal
        if local_multimodal and local_multimodal.is_available():
            image_description, error_message = local_multimodal.analyze_image_with_local_llm(contents, None)
        else:
            error_message = "Local multimodal module not available or imports missing."
    except Exception as e:
        error_message = f"Crash in image analysis: {str(e)}"
        print(f"Multimodal analysis error: {e}")

    # If it failed, TELL US WHY
    if not image_description:
        detailed_error = error_message if error_message else "Unknown error occurred."
        ai_response = f"I'm sorry, I couldn't see the image. The internal error was: [{detailed_error}]"
        
        mem.append_to_chat(chat_id, "human", f"[Image: {file.filename}] {question}", user_id=current_user)
        mem.append_to_chat(chat_id, "ai", ai_response, user_id=current_user)
        return ChatResponse(response=ai_response, chat_id=chat_id)

    # Step 2: Send Description to Brain
    print(f"🖼️ Vision Model saw: {image_description}")
    
    prompt_for_brain = (
        f"SYSTEM: The user uploaded an image. "
        f"The visual description is: '{image_description}'. "
        f"User's Question: '{question}'\n"
        "Answer the question using the visual description."
    )

    history_dicts = mem.get_chat_history(chat_id, user_id=current_user)
    langchain_history = []
    for h in history_dicts:
        if h["role"] == "human":
            langchain_history.append(HumanMessage(content=h["content"]))
        else:
            langchain_history.append(AIMessage(content=h["content"]))
    
    long_term_mem = mem.get_long_term_memory(user_id=current_user)

    final_answer = brain.get_brain_response(prompt_for_brain, langchain_history, long_term_mem)

    mem.append_to_chat(chat_id, "human", f"[Image: {file.filename}] {question}", user_id=current_user)
    mem.append_to_chat(chat_id, "ai", final_answer, user_id=current_user)

    return ChatResponse(response=final_answer, chat_id=chat_id)

@app.get("/status")
def service_status():
    try:
        from backend.brain import llm_services
        return llm_services.check_status()
    except Exception as e:
        return {"error": str(e)}

# =====================
# 4. VOICE ENDPOINTS (OPEN)
# =====================

@app.post("/stt")
async def speech_to_text(file: UploadFile = File(...)):
    uid = uuid.uuid4().hex
    webm_path = f"{uid}.webm"
    wav_path = f"{uid}.wav"
    clean_wav_path = f"{uid}_clean.wav"

    with open(webm_path, "wb") as f:
        f.write(await file.read())

    try:
        subprocess.run([
            FFMPEG_PATH, "-y", "-i", webm_path,
            "-ar", "16000", "-ac", "1",
            "-af", "highpass=f=200, lowpass=f=3000, afftdn, silenceremove=stop_periods=-1:stop_threshold=-50dB",
            clean_wav_path
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    except Exception as e:
        print(f"FFmpeg Error: {e}")
        return {"error": "FFmpeg conversion failed"}

    segments, _ = whisper_model.transcribe(clean_wav_path, language="en", vad_filter=True)
    text = " ".join(s.text for s in segments)

    for path in [webm_path, wav_path, clean_wav_path]:
        if os.path.exists(path):
            os.remove(path)

    return {"text": text.strip()}

@app.post("/tts")
async def text_to_speech(req: TTSRequest):
    text = req.text
    if not text.strip():
        return {"error": "No text provided"}

    clean_text = re.sub(r'[*#`_~]', '', text) 
    output_file = f"tts_{uuid.uuid4().hex}.mp3"
    
    communicate = edge_tts.Communicate(clean_text, "en-GB-RyanNeural")
    await communicate.save(output_file)
    
    with open(output_file, "rb") as f:
        audio_data = f.read()
    
    os.remove(output_file)
    
    return StreamingResponse(io.BytesIO(audio_data), media_type="audio/mpeg")

@app.websocket("/ws/agent")
async def agent_ws(ws: WebSocket):
    global connected_agent
    await ws.accept()
    connected_agent = ws
    print("🖥 Agent connected")
    
    try:
        while True:
            data = await ws.receive_text()
            print("Agent result:", data)
    except Exception as e:
        print("Agent disconnected:", e)
    finally:
        if connected_agent == ws:
            connected_agent = None


@app.get("/agent-status")
def agent_status():
    return {"connected": connected_agent is not None}


if __name__ == "__main__":
    import uvicorn
    print("🚀 JARVIS Backend running on http://127.0.0.1:8000")
    uvicorn.run(app, host="127.0.0.1", port=8000)