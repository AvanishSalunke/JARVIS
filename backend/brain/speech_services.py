import warnings
import os
import shutil
import sys
import torch
import torchaudio
import whisper
import soundfile as sf
import numpy as np

if not hasattr(torchaudio, "list_audio_backends"):
    def _list_audio_backends():
        return ["soundfile"]
    torchaudio.list_audio_backends = _list_audio_backends

from speechbrain.inference import EncoderClassifier
from transformers import SpeechT5Processor, SpeechT5ForTextToSpeech, SpeechT5HifiGan

warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Speech Services running on: {DEVICE}")

VOICE_FILENAME = "jarvis_voice.wav"
VOICES_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "voices")
REF_VOICE_PATH = os.path.join(VOICES_DIR, VOICE_FILENAME)

print("Loading Whisper model...")
stt_model = whisper.load_model("base", device=DEVICE)

print("Loading SpeechT5 models...")
processor = SpeechT5Processor.from_pretrained("microsoft/speecht5_tts")
tts_model = SpeechT5ForTextToSpeech.from_pretrained("microsoft/speecht5_tts").to(DEVICE)
vocoder = SpeechT5HifiGan.from_pretrained("microsoft/speecht5_hifigan").to(DEVICE)

print("Loading Voice Encoder...")
classifier = EncoderClassifier.from_hparams(
    source="speechbrain/spkrec-xvect-voxceleb", 
    savedir="pretrained_xvect",
    run_opts={"device": DEVICE}
)

def get_speaker_embedding(path):
    if os.path.exists(path):
        try:
            signal, fs = torchaudio.load(path)
            if fs != 16000:
                transform = torchaudio.transforms.Resample(orig_freq=fs, new_freq=16000)
                signal = transform(signal)
            
            with torch.no_grad():
                embeddings = classifier.encode_batch(signal)
                embeddings = torch.nn.functional.normalize(embeddings, dim=2)
                xvec = embeddings.squeeze().mean(dim=0).unsqueeze(0)
                if xvec.shape[-1] > 512:
                    xvec = xvec[:, :512]
            
            print(f"Loaded Voice Profile: {path}")
            return xvec.to(DEVICE)
        except Exception as e:
            print(f"Error loading voice file: {e}")
    
    print("Using Default System Voice (Randomized)")
    return torch.randn(1, 512).to(DEVICE)

SPEAKER_EMBEDDING = get_speaker_embedding(REF_VOICE_PATH)

def transcribe_audio(file_path: str):
    try:
        abs_path = os.path.abspath(file_path)
        if not os.path.exists(abs_path):
            return "Error: Audio file missing."
            
        result = stt_model.transcribe(abs_path, fp16=False)
        text = result["text"].strip()
        return text if text else "..."
    except Exception as e:
        print(f"Transcription Error: {e}")
        return "..."

def generate_speech(text: str, output_file: str):
    if not text:
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