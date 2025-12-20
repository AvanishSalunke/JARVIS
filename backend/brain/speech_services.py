import torch
import torchaudio
import whisper
import os
import soundfile as sf

# --- 🛠️ CRITICAL FIX: PATCH FOR TORCHAUDIO ERROR ---
# This forces the code to work even if Torchaudio is too new
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
REF_VOICE_PATH = os.path.join("voices", REF_VOICE_NAME)

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
    """Creates the 'digital fingerprint' of the voice you want to copy."""
    if not os.path.exists(path):
        print(f"⚠️ Voice file not found at: {path}. Using random voice.")
        # Return a random embedding if file is missing (prevents crash)
        return torch.randn(1, 512).to(DEVICE)
        
    signal, sr = torchaudio.load(path)
    if sr != 16000:
        signal = torchaudio.functional.resample(signal, sr, 16000)
    
    with torch.no_grad():
        xvec = classifier.encode_batch(signal)
        xvec = xvec.squeeze().mean(dim=0).unsqueeze(0)
        
    return xvec.to(DEVICE)

# Load the voice fingerprint
try:
    SPEAKER_EMBEDDING = get_speaker_embedding(REF_VOICE_PATH)
    print("✅ Jarvis Voice Loaded Successfully!")
except Exception as e:
    print(f"⚠️ Warning: Voice Error: {e}")
    SPEAKER_EMBEDDING = None

# --- Main Functions ---

def transcribe_audio(file_path: str):
    """Takes an audio file path, returns text."""
    try:
        result = stt_model.transcribe(file_path)
        return result["text"].strip()
    except Exception as e:
        print(f"Error in transcription: {e}")
        return ""

def generate_speech(text: str, output_file="response.wav"):
    """Takes text, creates an audio file."""
    if SPEAKER_EMBEDDING is None:
        print("Error: No speaker embedding found.")
        return None

    inputs = processor(text=text, return_tensors="pt").to(DEVICE)
    
    with torch.no_grad():
        audio = tts_model.generate_speech(
            inputs["input_ids"], 
            SPEAKER_EMBEDDING, 
            vocoder=vocoder
        )
    
    sf.write(output_file, audio.cpu().numpy(), 16000)
    return output_file  