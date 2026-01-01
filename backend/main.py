import os
import io
import uuid
import subprocess
import asyncio
import edge_tts  
import re

from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from faster_whisper import WhisperModel

# Import your existing brain modules
from brain.llm_services import get_brain_response
from brain.memory_services import (
    get_vector_store,
    search_memory,
    add_text_to_memory
)
from langchain_core.messages import HumanMessage, AIMessage

# =====================
# CONFIG
# =====================

# Ensure this path is correct for your system
FFMPEG_PATH = r"C:\ffmpeg\bin\ffmpeg.exe"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# =====================
# FASTAPI APP
# =====================

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# =====================
# MEMORY INIT
# =====================

vector_store = get_vector_store()
chat_history = []   # In-memory history

# =====================
# SPEECH TO TEXT (WHISPER)
# =====================

# "base.en" is faster than "small" and very accurate for English
WHISPER_MODEL_SIZE = "base.en"

whisper_model = WhisperModel(
    WHISPER_MODEL_SIZE,
    device="cpu",
    compute_type="int8"
)

@app.post("/stt")
async def speech_to_text(file: UploadFile = File(...)):
    uid = uuid.uuid4().hex
    webm_path = f"{uid}.webm"
    wav_path = f"{uid}.wav"

    # 1. Save the uploaded file
    with open(webm_path, "wb") as f:
        f.write(await file.read())

    # 2. Convert WebM to WAV using FFMPEG
    try:
        subprocess.run(
            [
                FFMPEG_PATH,
                "-y",
                "-i", webm_path,
                "-ar", "16000",
                "-ac", "1",
                wav_path
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True
        )
    except FileNotFoundError:
        return {"error": "FFmpeg not found. Check FFMPEG_PATH."}

    # 3. Transcribe
    segments, info = whisper_model.transcribe(
        wav_path,
        language="en",
        vad_filter=True
    )

    text = " ".join(segment.text for segment in segments)

    # 4. Cleanup temp files
    if os.path.exists(webm_path):
        os.remove(webm_path)
    if os.path.exists(wav_path):
        os.remove(wav_path)

    return {"text": text.strip()}


# =====================
# CHAT ENDPOINT (LLM)
# =====================

class ChatRequest(BaseModel):
    text: str

class ChatResponse(BaseModel):
    response: str

@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    user_text = req.text

    # Retrieve relevant memory
    memories = search_memory(user_text, vector_store)

    # Get LLM response
    response = get_brain_response(
        user_input=user_text,
        chat_history=chat_history,
        long_term_memory=memories
    )

    # Update history
    chat_history.append(HumanMessage(content=user_text))
    chat_history.append(AIMessage(content=response))

    # Store memory if substantial
    if len(user_text) > 20:
        add_text_to_memory(user_text, vector_store)

    return ChatResponse(response=response)

# =====================
# CLEAN & FAST TTS
# =====================

TTS_VOICE = "en-GB-RyanNeural"

@app.post("/tts")
async def text_to_speech(text: str):
    if not text.strip():
        return {"error": "No text provided"}

    # 1. CLEANING: Remove Markdown symbols (*, #, _, etc.)
    # This regex removes asterisks, hashes, and backticks so TTS doesn't read them.
    clean_text = re.sub(r'[\*\#`_]', '', text) 
    
    # Optional: Remove emojis if they sound weird (uncomment if needed)
    # clean_text = re.sub(r'[^\w\s,!.?]', '', clean_text)

    # 2. Generate Audio
    output_file = f"tts_{uuid.uuid4().hex}.mp3"
    communicate = edge_tts.Communicate(clean_text, TTS_VOICE)
    
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
    print("Starting JARVIS Backend on http://127.0.0.1:8000")
    uvicorn.run(app, host="127.0.0.1", port=8000)