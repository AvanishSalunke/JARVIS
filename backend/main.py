import sys
import pathlib
import json  # Added for parsing the "sticky note" JSON

# Allow running this file directly from the `backend/` directory for convenience.
if __package__ is None:
    repo_root = pathlib.Path(__file__).resolve().parent.parent
    repo_root_str = str(repo_root)
    if repo_root_str not in sys.path:
        sys.path.insert(0, repo_root_str)

import os
import io
import uuid
import subprocess
import edge_tts 
import re
from fastapi import FastAPI, UploadFile, File, HTTPException, Body, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, List

# =====================
# IMPORTS
# =====================
from backend.brain import memory_manager as mem
from backend.brain import llm_services as brain
from backend.brain import web_search as searcher  # <--- NEW IMPORT
from langchain_core.messages import HumanMessage, AIMessage
from faster_whisper import WhisperModel

# =====================
# CONFIG
# =====================
import shutil
FFMPEG_PATH = shutil.which("ffmpeg") or r"C:\ffmpeg\bin\ffmpeg.exe"
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load Whisper once on startup
print("⏳ Loading Whisper Model...")
whisper_model = WhisperModel("small.en", device="cpu", compute_type="int8")
print("✅ Whisper Model Loaded!")

# Preload multimodal model
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

# =====================
# HELPER FUNCTIONS
# =====================

def perform_search(query):
    """
    Executes the real web search using the tool from web_searcher.py
    """
    print(f"🔎 Jarvis is searching the web for: {query}")
    
    # Get the tool from your new web_searcher.py
    tool = searcher.get_search_tool()
    
    try:
        # Run the search
        result = tool.func(query)
        # Trim if result is massive to save tokens
        return str(result)[:2000] if len(str(result)) > 2000 else str(result)
    except Exception as e:
        print(f"❌ Search Error: {e}")
        return "I attempted to search but encountered an error."

# =====================
# 1. MANAGEMENT ENDPOINTS
# =====================

@app.get("/chats")
def list_chats():
    return mem.get_all_chats()

@app.post("/chats/new")
def create_chat():
    return mem.create_new_chat()

@app.put("/chats/{chat_id}")
def rename_chat(chat_id: str, req: RenameRequest):
    success = mem.rename_chat(chat_id, req.new_name)
    if not success:
        raise HTTPException(status_code=404, detail="Chat not found")
    return {"status": "success", "new_name": req.new_name}

@app.delete("/chats/{chat_id}")
def delete_chat(chat_id: str):
    success = mem.delete_chat(chat_id)
    if not success:
        raise HTTPException(status_code=404, detail="Chat not found")
    return {"status": "success"}

@app.get("/chats/{chat_id}/history")
def get_history(chat_id: str):
    return mem.get_chat_history(chat_id)

# =====================
# 2. CHAT & BRAIN ENDPOINT (UPDATED FOR SEARCH)
# =====================

@app.post("/chat", response_model=ChatResponse)
def chat_endpoint(req: ChatRequest):
    user_text = req.text
    chat_id = req.chat_id

    if not chat_id:
        new_chat = mem.create_new_chat()
        chat_id = new_chat["chat_id"]

    # 1. Get History
    history_dicts = mem.get_chat_history(chat_id)
    langchain_history = []
    for h in history_dicts:
        if h["role"] == "human":
            langchain_history.append(HumanMessage(content=h["content"]))
        else:
            langchain_history.append(AIMessage(content=h["content"]))

    # 2. Get LTM
    long_term_mem = mem.get_long_term_memory()

    # 3. FIRST CALL TO BRAIN
    ai_response = brain.get_brain_response(user_text, langchain_history, long_term_mem)

    # 4. CHECK FOR TOOL CALL (The "Sticky Note")
    # We look for a JSON object containing "query"
    final_answer = ai_response
    
    try:
        if "{" in ai_response and "query" in ai_response:
            # Try to parse the JSON
            start_index = ai_response.find("{")
            end_index = ai_response.rfind("}") + 1
            json_str = ai_response[start_index:end_index]
            
            tool_data = json.loads(json_str)
            
            if "query" in tool_data:
                search_query = tool_data["query"]
                
                # PERFORM THE SEARCH
                search_results = perform_search(search_query)
                
                # 5. SECOND CALL TO BRAIN (With results)
                # We feed the search results back as a system message or a new user prompt
                search_context = f"SYSTEM: I have searched Google. Here are the results: {search_results}\n\nUsing these results, answer the user's original question."
                
                # Append the "thought" process to history temporarily for this request
                langchain_history.append(HumanMessage(content=user_text))
                langchain_history.append(AIMessage(content=ai_response)) # The JSON request
                
                final_answer = brain.get_brain_response(search_context, langchain_history, long_term_mem)
    except Exception as e:
        print(f"⚠️ Tool call parsing failed, returning original response. Error: {e}")
        # If parsing fails, we just return the original text (which might be raw JSON, but better than crashing)
        final_answer = ai_response

    # 6. Save to DB (Only the final human text and final AI answer)
    mem.append_to_chat(chat_id, "human", user_text)
    mem.append_to_chat(chat_id, "ai", final_answer)

    # 7. Auto-Save "My Name is"
    if "my name is" in user_text.lower():
        mem.add_long_term_memory(f"User Mentioned: {user_text}")

    return ChatResponse(response=final_answer, chat_id=chat_id)

# =====================
# 3. IMAGE QUESTION ENDPOINT
# =====================
@app.post("/image_qa", response_model=ChatResponse)
async def image_question(file: UploadFile = File(...), question: str = Form(...), chat_id: Optional[str] = Form(None)):
    if not chat_id:
        new_chat = mem.create_new_chat()
        chat_id = new_chat["chat_id"]

    contents = await file.read()

    # Step 1: Get the Image Description
    image_description = None
    error_message = None  # Store the error
    
    try:
        from backend.brain import local_multimodal
        if local_multimodal and local_multimodal.is_available():
            # Pass None to get a generic description
            image_description, error_message = local_multimodal.analyze_image_with_local_llm(contents, None)
        else:
            error_message = "Local multimodal module not available or imports missing."
            
    except Exception as e:
        error_message = f"Crash in image analysis: {str(e)}"
        print(f"Multimodal analysis error: {e}")

    # If it failed, TELL US WHY
    if not image_description:
        # Use the actual error message if we have one
        detailed_error = error_message if error_message else "Unknown error occurred."
        ai_response = f"I'm sorry, I couldn't see the image. The internal error was: [{detailed_error}]"
        
        mem.append_to_chat(chat_id, "human", f"[Image: {file.filename}] {question}")
        mem.append_to_chat(chat_id, "ai", ai_response)
        return ChatResponse(response=ai_response, chat_id=chat_id)

    # Step 2: Send Description to Brain
    print(f"🖼️ Vision Model saw: {image_description}")
    
    prompt_for_brain = (
        f"SYSTEM: The user uploaded an image. "
        f"The visual description is: '{image_description}'. "
        f"User's Question: '{question}'\n"
        "Answer the question using the visual description."
    )

    history_dicts = mem.get_chat_history(chat_id)
    langchain_history = []
    for h in history_dicts:
        if h["role"] == "human":
            langchain_history.append(HumanMessage(content=h["content"]))
        else:
            langchain_history.append(AIMessage(content=h["content"]))
    
    long_term_mem = mem.get_long_term_memory()

    final_answer = brain.get_brain_response(prompt_for_brain, langchain_history, long_term_mem)

    mem.append_to_chat(chat_id, "human", f"[Image: {file.filename}] {question}")
    mem.append_to_chat(chat_id, "ai", final_answer)

    return ChatResponse(response=final_answer, chat_id=chat_id)

@app.get("/status")
def service_status():
    try:
        from backend.brain import llm_services
        return llm_services.check_status()
    except Exception as e:
        return {"error": str(e)}

# =====================
# 4. VOICE ENDPOINTS
# =====================

@app.post("/stt")
async def speech_to_text(file: UploadFile = File(...)):
    uid = uuid.uuid4().hex
    webm_path = f"{uid}.webm"
    wav_path = f"{uid}.wav"
    clean_wav_path = f"{uid}_clean.wav"

    # Save uploaded file
    with open(webm_path, "wb") as f:
        f.write(await file.read())

    try:
        # Convert webm -> wav (16kHz mono) with noise reduction and trimming silence
        # -af "highpass, lowpass, afftdn, silenceremove"
        # highpass & lowpass: filter extreme frequencies
        # afftdn: noise reduction
        # silenceremove: trims silence at start/end
        subprocess.run([
            FFMPEG_PATH, "-y", "-i", webm_path,
            "-ar", "16000", "-ac", "1",
            "-af", "highpass=f=200, lowpass=f=3000, afftdn, silenceremove=stop_periods=-1:stop_threshold=-50dB",
            clean_wav_path
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    except Exception as e:
        print(f"FFmpeg Error: {e}")
        return {"error": "FFmpeg conversion failed"}

    # Transcribe with Whisper (VAD optional)
    segments, _ = whisper_model.transcribe(clean_wav_path, language="en", vad_filter=True)
    text = " ".join(s.text for s in segments)

    # Cleanup files
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

# =====================
# RUNNER
# =====================
if __name__ == "__main__":
    import uvicorn
    print("🚀 JARVIS Backend running on http://127.0.0.1:8000")
    uvicorn.run(app, host="127.0.0.1", port=8000)