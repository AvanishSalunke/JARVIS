import os
import shutil
import time
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Import our modules
from brain.llm_services import get_brain_response
from brain.memory_services import search_memory, get_vector_store
from brain.speech_services import transcribe_audio, generate_speech

app = FastAPI(title="JARVIS API")

# 1. Allow React to talk to this Server (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins (good for development)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Setup Static Files (To serve the generated audio)
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize Memory DB
vector_store = get_vector_store()
chat_history = []  # Simple in-memory history for now

class TextRequest(BaseModel):
    text: str

@app.get("/")
def health_check():
    return {"status": "Jarvis is Online"}

@app.post("/chat-text")
def chat_text_only(request: TextRequest):
    """Debug endpoint: Chat without voice."""
    
    # 1. Search Long Term Memory
    relevant_memory = search_memory(request.text, vector_store)
    
    # 2. Get Brain Response
    response = get_brain_response(request.text, chat_history, relevant_memory)
    
    # 3. Update Short Term History
    chat_history.append(("human", request.text))
    chat_history.append(("ai", response))
    
    return {"response": response, "memory_used": relevant_memory}

@app.post("/process-voice")
async def process_voice(file: UploadFile = File(...)):
    """Main Endpoint: Receives Audio -> Returns Audio + Text"""
    
    # 1. Save the incoming audio file temporarily
    temp_filename = f"temp_{int(time.time())}.wav"
    with open(temp_filename, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    try:
        # 2. Transcribe (Ears)
        print(f"🎧 Hearing audio: {temp_filename}")
        user_text = transcribe_audio(temp_filename)
        print(f"🗣️ User said: {user_text}")
        
        if not user_text:
            return {"error": "No speech detected"}

        # 3. Think (Brain & Memory)
        relevant_memory = search_memory(user_text, vector_store)
        response_text = get_brain_response(user_text, chat_history, relevant_memory)
        print(f"🧠 Jarvis thinks: {response_text}")

        # 4. Speak (Voice)
        # We save output to 'static' folder so frontend can download it
        output_filename = f"response_{int(time.time())}.wav"
        output_path = os.path.join("static", output_filename)
        
        generate_speech(response_text, output_path)
        
        # 5. Cleanup
        chat_history.append(("human", user_text))
        chat_history.append(("ai", response_text))
        os.remove(temp_filename) # Delete input file to save space

        # Return the URL to the audio file
        return {
            "user_text": user_text,
            "jarvis_text": response_text,
            "audio_url": f"http://127.0.0.1:8000/static/{output_filename}"
        }

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)