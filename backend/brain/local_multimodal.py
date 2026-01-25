import io
import os
from PIL import Image

# Global variables to cache the model so we don't reload it every time
_model = None
_processor = None
# We use Salesforce BLIP. It's fast, accurate, and downloads automatically.
_model_name = "Salesforce/blip-image-captioning-large"

def is_available():
    """Checks if the necessary libraries are installed."""
    try:
        import torch
        import transformers
        from PIL import Image
        return True
    except ImportError:
        return False

def _init_model():
    """Loads the model into memory. Called once on startup by main.py."""
    global _model, _processor
    
    if _model is not None:
        return  # Already loaded

    print(f"⏳ Loading Vision Model ({_model_name})... this may take a moment...")
    try:
        from transformers import BlipProcessor, BlipForConditionalGeneration
        
        # Load processor and model (downloads automatically if not found)
        _processor = BlipProcessor.from_pretrained(_model_name)
        _model = BlipForConditionalGeneration.from_pretrained(_model_name)
        print("✅ Vision Model Loaded Successfully!")
    except Exception as e:
        print(f"❌ Failed to load Vision Model: {e}")

def analyze_image_with_local_llm(image_bytes, user_question=None):
    """
    Takes raw image bytes and a user question (optional).
    Returns (answer_string, error_string).
    """
    global _model, _processor

    # 1. Ensure model is loaded
    if _model is None:
        _init_model()
    
    if _model is None:
        return None, "Vision model could not be loaded."

    try:
        # 2. Convert bytes to PIL Image
        raw_image = Image.open(io.BytesIO(image_bytes)).convert('RGB')

        # 3. Prepare inputs
        # If the user asked a specific question, we condition the generation on that text.
        text_input = user_question if user_question else "a photography of"
        
        inputs = _processor(raw_image, text_input, return_tensors="pt")

        # 4. Generate response
        out = _model.generate(**inputs, max_new_tokens=50)
        
        # 5. Decode
        caption = _processor.decode(out[0], skip_special_tokens=True)
        
        return caption, None

    except Exception as e:
        print(f"Error processing image: {e}")
        return None, str(e)