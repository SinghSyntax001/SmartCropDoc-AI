# Location: SmartCropDoc-AI/app/services/enhancer.py (Refined for Testing)

import io
import random
from PIL import Image
import numpy as np
import cv2 
import base64
import torch
from realesrgan import RealESRGANer
from basicsr.archs.rrdbnet_arch import RRDBNet
# Note: You need to ensure the imports for basicsr/rrdbnet_arch are correct based on your pip install.

# --- Configuration ---
DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
MODEL_PATH = 'models/enhancer_weights/RealESRGAN_x4plus.pth' 
SCALE_FACTOR = 4
BLUR_VARIANCE_THRESHOLD = 8.0 

# --- Model Loading ---
def load_real_esrgan_model():
    """Loads the Real-ESRGAN model once and caches it."""
    try:
        # Define the model structure
        model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, 
                        num_block=23, num_grow_ch=32, scale=SCALE_FACTOR)
        
        # Create the inference wrapper
        upsampler = RealESRGANer(
            scale=SCALE_FACTOR,
            model_path=MODEL_PATH,
            model=model,
            tile=0, # Optimal setting for quick, small image inference
            tile_pad=10,
            pre_pad=0,
            half=False, 
            device=DEVICE
        )
        print(f"Real-ESRGAN Model Loaded on: {DEVICE}")
        return upsampler
    except Exception as e:
        print(f"ERROR: Failed to load Real-ESRGAN model! Check path/dependencies. {e}")
        return None

# --- Core Logic ---
def check_image_quality(image_bytes: bytes) -> bool:
    """Analyzes an image to determine if enhancement is necessary (Blur Check)."""
    try:
        # Convert to grayscale for blur check
        img_np = np.array(Image.open(io.BytesIO(image_bytes)).convert("L")) 
        laplacian_variance = cv2.Laplacian(img_np, cv2.CV_64F).var()
        
        is_blurred = laplacian_variance < BLUR_VARIANCE_THRESHOLD
        
        if is_blurred:
             return True
        return False
        
    except Exception:
        return False

def enhance_image(image_bytes: bytes, upsampler_instance, force_run: bool = False) -> bytes:
    """
    Runs Real-ESRGAN inference. Returns enhanced image bytes or original bytes.
    Added 'force_run' flag to bypass quality check during development/testing.
    """
    
    if not upsampler_instance:
        print("Error: Enhancer model instance is missing.")
        return image_bytes

    if not force_run and not check_image_quality(image_bytes):
        print("Enhancement skipped based on quality check.")
        return image_bytes

    # --- If force_run=True OR check_image_quality=True, the code proceeds here ---
    print(f"--- Running Enhancement (Scale: {SCALE_FACTOR}x) ---")
    
    try:
        # 1. Decode image_bytes to NumPy array
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        img_np = np.array(img)
        
        # 2. Run Inference
        output, _ = upsampler_instance.enhance(img_np, outscale=SCALE_FACTOR)
        
        # 3. Convert enhanced output (NumPy array) back to PNG bytes
        enhanced_pil = Image.fromarray(output)
        enhanced_buffer = io.BytesIO()
        enhanced_pil.save(enhanced_buffer, format="PNG")
        
        print("Enhancement complete.")
        return enhanced_buffer.getvalue()
        
    except Exception as e:
        print(f"Real-ESRGAN inference failed at runtime: {e}. Returning original image.")
        return image_bytes