import os
import sys
from PIL import Image
import io
import time
import base64


sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.services.enhancer import load_real_esrgan_model, enhance_image

def run_standalone_test(input_path: str):
    """
    Loads the enhancer model, processes the input image, and saves the enhanced output.
    
    Args:
        input_path: Path to the blurred image file to be enhanced.
    """
    if not os.path.exists(input_path):
        print(f"🛑 ERROR: Input file not found at path: {input_path}")
        return

    print("--- SmartCropDoc-AI Image Enhancement Test ---")
    
    # 1. Load the Model (Uses CPU/CUDA configured in enhancer.py)
    start_time = time.time()
    enhancer_model = load_real_esrgan_model()
    
    if enhancer_model is None:
        print("\n❌ TEST FAILED: Model initialization failed. Check model path and PyTorch installation.")
        return

    model_load_time = time.time() - start_time
    print(f"Model loaded successfully in {model_load_time:.2f} seconds.")

    # 2. Prepare Input Image Bytes
    with open(input_path, "rb") as f:
        original_bytes = f.read()
    
    input_size_kb = len(original_bytes) / 1024
    print(f"\nProcessing input: {os.path.basename(input_path)} ({input_size_kb:.2f} KB)")
    
    # 3. Run Enhancement Pipeline
    start_time = time.time()
    # PASS force_run=True HERE to bypass the quality check logic entirely
    enhanced_bytes = enhance_image(original_bytes, enhancer_model, force_run=True) 
    inference_time = time.time() - start_time
    
    # Determine output file path
    base_name, ext = os.path.splitext(input_path)
    output_path = f"{base_name}_ENHANCED.png"
    
    # Check if enhancement was actually performed (size check)
    if len(enhanced_bytes) == len(original_bytes):
        print("⚠️ WARNING: Enhancement was skipped (Image quality deemed sufficient or failed at runtime).")
        output_path = f"{base_name}_SKIPPED.png"

    # 4. Save Output and Report
    with open(output_path, "wb") as f:
        f.write(enhanced_bytes)
        
    output_size_kb = len(enhanced_bytes) / 1024
    
    print("\n✅ TEST SUCCESSFUL:")
    print(f"   -> Output Saved To: {output_path}")
    print(f"   -> Input Size: {input_size_kb:.2f} KB")
    print(f"   -> Output Size: {output_size_kb:.2f} KB")
    print(f"   -> Inference Time: {inference_time:.2f} seconds")
    print("\n[Action] Open the output file and compare it visually with your original input.")


if __name__ == "__main__":
    # --- USAGE ---
    if len(sys.argv) < 2:
        print("\nUSAGE: python test_enhance_standalone.py <path/to/your/blurred_image.jpg>")
        print("\nExample: python test_enhance_standalone.py my_low_res_leaf.jpg")
    else:
        input_file = sys.argv[1]
        run_standalone_test(input_file)