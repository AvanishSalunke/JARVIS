import torch
import torchaudio
import whisper
import os
import soundfile as sf
import numpy as np

# --- 🛠️ CRITICAL FIX: PATCH FOR TORCHAUDIO ERROR ---
if not hasattr(torchaudio, "list_audio_backends"):
    def _list_audio_backends():
        return ["soundfile"]
    torchaudio.list_audio_backends = _list_audio_backends
# ---------------------------------------------------

from speechbrain.inference import EncoderClassifier
from transformers import SpeechT5Processor, SpeechT5ForTextToSpeech, SpeechT5HifiGan

# --- Configuration ---
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
print(f"🚀 Speech Services running on: {DEVICE}")

# PATHS
REF_VOICE_NAME = "caged_trs7_0.wav"  
# We look for the voice file relative to THIS file's location or the backend root
REF_VOICE_PATH = os.path.join(os.path.dirname(__file__), "..", "voices", REF_VOICE_NAME)

# --- Load Models (Startup) ---
print("⏳ Loading Whisper (Ears)...")
stt_model = whisper.load_model("base", device=DEVICE)

print("⏳ Loading SpeechT5 (Voice)...")
processor = SpeechT5Processor.from_pretrained("microsoft/speecht5_tts")
tts_model = SpeechT5ForTextToSpeech.from_pretrained("microsoft/speecht5_tts").to(DEVICE)
vocoder = SpeechT5HifiGan.from_pretrained("microsoft/speecht5_hifigan").to(DEVICE)

print("⏳ Loading Voice Encoder...")
classifier = EncoderClassifier.from_hparams(
    source="speechbrain/spkrec-xvect-voxceleb", 
    savedir="pretrained_xvect",
    run_opts={"device": DEVICE}
)

# --- Helper: Load Speaker Embedding ---
def get_speaker_embedding(path):
    """Creates the 'digital fingerprint' of the voice."""
    # 1. Try to load the real file
    if os.path.exists(path):
        try:
            signal, sr = torchaudio.load(path)
            # Resample if needed
            if sr != 16000:
                signal = torchaudio.functional.resample(signal, sr, 16000)
            
            # Squeeze to ensure it's a 1D tensor [samples]
            signal = signal.squeeze() 
            
            # Encode
            with torch.no_grad():
                xvec = classifier.encode_batch(signal)
                xvec = xvec.squeeze().mean(dim=0).unsqueeze(0)
            return xvec.to(DEVICE)
        except Exception as e:
            print(f"⚠️ Error processing voice file: {e}")

    # 2. Fallback: Generate a random voice (Prevent Crash)
    print(f"⚠️ Voice file not found or failed: {path}. Using RANDOM voice.")
    # Create a random embedding of size (1, 512)
    random_voice = torch.randn(1, 512).to(DEVICE)
    return random_voice

# Initialize Voice
SPEAKER_EMBEDDING = get_speaker_embedding(REF_VOICE_PATH)
print("✅ Jarvis Voice Ready (Real or Random).")

# --- Main Functions ---

def transcribe_audio(file_path: str):
    """Takes an audio file path, returns text."""
    try:
        # Whisper needs absolute paths sometimes on Windows
        abs_path = os.path.abspath(file_path)
        result = stt_model.transcribe(abs_path, fp16=False) # fp16=False fixes the CPU warning
        text = result["text"].strip()
        return text if text else "..."
    except Exception as e:
        print(f"❌ Error in transcription: {e}")
        return "I could not hear you."

def generate_speech(text: str, output_file: str):
    """Takes text, creates an audio file."""
    if not text:
        return None

    print(f"Generating audio for: {text}")
    
    # Use the GLOBAL speaker embedding (which is now guaranteed to exist)
    inputs = processor(text=text, return_tensors="pt").to(DEVICE)
    
    with torch.no_grad():
        audio = tts_model.generate_speech(
            inputs["input_ids"], 
            SPEAKER_EMBEDDING, 
            vocoder=vocoder
        )
    
    sf.write(output_file, audio.cpu().numpy(), 16000)
    return output_file