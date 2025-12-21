import uvicorn  # <-- NEW IMPORT
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import shutil
import os

# Import your brain
from brain.speech_services import transcribe_audio, generate_speech

app = FastAPI()

# 1. Allow React to talk to Python (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. MOUNT THE AUDIO FOLDER
os.makedirs("generated_audio", exist_ok=True)
app.mount("/audio", StaticFiles(directory="generated_audio"), name="audio")

@app.get("/")
def read_root():
    return {"status": "Jarvis is Online"}

@app.post("/process-voice")
async def process_voice(file: UploadFile = File(...)):
    # Save the user's recording temporarily
    temp_filename = "temp_input.webm"
    with open(temp_filename, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # 1. Listen (Speech to Text)
    user_text = transcribe_audio(temp_filename)
    print(f"User said: {user_text}")

    # 2. Think (AI Brain) - Simple echo for now
    jarvis_response = f"You said: {user_text}. I am fully operational."
    
    # 3. Speak (Text to Speech)
    output_filename = "response.wav"
    file_path = os.path.join("generated_audio", output_filename)
    
    generate_speech(jarvis_response, file_path)

    # Return the data + the PUBLIC URL for the audio
    return {
        "user_text": user_text,
        "jarvis_text": jarvis_response,
        "audio_url": f"http://127.0.0.1:8000/audio/{output_filename}" 
    }

# --- 🚀 THE MISSING PART: START THE SERVER ---
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)