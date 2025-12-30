import os
import io
import uuid
import json
import subprocess

import torch
import numpy as np
import soundfile as sf

from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from faster_whisper import WhisperModel

from transformers import (
    SpeechT5Processor,
    SpeechT5ForTextToSpeech,
    SpeechT5HifiGan
)

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

FFMPEG_PATH = r"C:\ffmpeg\bin\ffmpeg.exe"
BASE_DIR = r"C:\Users\praty\OneDrive\Desktop\Jarvis\JARVIS\backend"

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
# 🔹 ADDED: MEMORY INIT
# =====================

vector_store = get_vector_store()
chat_history = []   # In-memory (OK for now)

# =====================
# SPEECH TO TEXT (WHISPER)
# =====================

WHISPER_MODEL_SIZE = "small"  # tiny | base | small | medium | large-v3

whisper_model = WhisperModel(
    WHISPER_MODEL_SIZE,
    device="cpu",
    compute_type="int8"  # best for CPU
)
@app.post("/stt")
async def speech_to_text(file: UploadFile = File(...)):
    uid = uuid.uuid4().hex
    webm_path = f"{uid}.webm"
    wav_path = f"{uid}.wav"

    with open(webm_path, "wb") as f:
        f.write(await file.read())

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

    segments, info = whisper_model.transcribe(
        wav_path,
        language="en",
        vad_filter=True
    )

    text = " ".join(segment.text for segment in segments)

    os.remove(webm_path)
    os.remove(wav_path)

    return {"text": text.strip()}


# =====================
# 🔹 ADDED: CHAT ENDPOINT (LLM)
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

    # Store memory (basic rule)
    if len(user_text) > 20:
        add_text_to_memory(user_text, vector_store)

    return ChatResponse(response=response)

# =====================
# TEXT TO SPEECH (SpeechT5)
# =====================

embedding_path = r"C:\Users\praty\OneDrive\Desktop\Jarvis\JARVIS\backend\TextToSpeech\speaker_embedding.txt"
embedding = np.loadtxt(embedding_path)
speaker_embedding = torch.tensor(embedding, dtype=torch.float32).unsqueeze(0)

processor = SpeechT5Processor.from_pretrained("microsoft/speecht5_tts")
tts_model = SpeechT5ForTextToSpeech.from_pretrained("microsoft/speecht5_tts")
vocoder = SpeechT5HifiGan.from_pretrained("microsoft/speecht5_hifigan")

@app.post("/tts")
def text_to_speech(text: str):
    inputs = processor(text=text, return_tensors="pt")

    speech = tts_model.generate_speech(
        inputs["input_ids"],
        speaker_embeddings=speaker_embedding
    )

    audio = vocoder(speech).detach().cpu().numpy().squeeze()
    audio = np.clip(audio, -1.0, 1.0)

    buffer = io.BytesIO()
    sf.write(buffer, audio, samplerate=16000, format="WAV")
    buffer.seek(0)

    return StreamingResponse(buffer, media_type="audio/wav")
