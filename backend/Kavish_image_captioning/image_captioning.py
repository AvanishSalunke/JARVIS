import torch
from PIL import Image
from transformers import BlipProcessor, BlipForConditionalGeneration
import requests

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Using device: {device}")
processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-large")
model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-large").to(device)
try:
    img_path = "image2.jpg"
    raw_image = Image.open(img_path).convert('RGB')
    
    # Example for a web image:
    # url = 'https://storage.googleapis.com/sfr-vision-language-research/BLIP/demo.jpg' 
    # raw_image = Image.open(requests.get(url, stream=True).raw).convert('RGB')

    inputs = processor(raw_image, return_tensors="pt").to(device)

    out = model.generate(**inputs, max_new_tokens=80)

    caption = processor.decode(out[0], skip_special_tokens=True)

    print("---")
    print(f"Generated Caption: {caption}")
    print("---")

except FileNotFoundError:
    print(f"Error: Image file not found at {img_path}")
    print("Please make sure the file exists or provide the full path.")