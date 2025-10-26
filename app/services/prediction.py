import torch
import torch.nn.functional as F
from torchvision import models, transforms
from PIL import Image
import numpy as np
import cv2 
import io
import base64

# --- Constants and Data (Ensure these match your training output) ---
DISEASE_CLASSES = [
    "Apple_Black_rot",
    "Apple_Cedar_apple_rust",
    "Apple_healthy",
    "Apple_scab"
]
NUM_CLASSES = len(DISEASE_CLASSES)
IMG_SIZE = 224 
MODEL_WEIGHTS_PATH = 'models/mobilenetv3_best.pth'

# --- Model Loading (Crucial for FastAPI Startup) ---

def load_mobilenet_model():
    """
    Loads the custom-trained MobileNetV3-Large model and prepares for inference.
    """
    try:
        # 1. Instantiate the MobileNetV3-Large architecture
        # Use models.MobileNet_V3_Large_Weights.DEFAULT if you use pre-trained weights for transfer learning
        model = models.mobilenet_v3_large(weights=None) 
        
        # 2. Adjust the final classifier layer
        num_ftrs = model.classifier[-1].in_features
        model.classifier[-1] = torch.nn.Linear(num_ftrs, NUM_CLASSES)
        
        # 3. Load your custom trained state_dict
        # NOTE: map_location='cpu' ensures it runs even if CUDA is not initialized, 
        # but the main FastAPI startup should handle the device placement.
        state_dict = torch.load(MODEL_WEIGHTS_PATH, map_location=torch.device('cpu'))
        model.load_state_dict(state_dict)
        
        model.eval() # Set model to inference mode
        print("MobileNetV3 Disease Classifier Loaded successfully.")
        return model
    except FileNotFoundError:
        print(f"ERROR: Model weights not found at {MODEL_WEIGHTS_PATH}. Using dummy initialization.")
        # Fallback: Initialize with random weights if the file is missing during development
        model = models.mobilenet_v3_large(weights=None)
        num_ftrs = model.classifier[-1].in_features
        model.classifier[-1] = torch.nn.Linear(num_ftrs, NUM_CLASSES)
        model.eval()
        return model
    except Exception as e:
        print(f"FATAL ERROR loading MobileNetV3: {e}")
        return None

# --- Preprocessing and Utilities ---

def preprocess_image(image_bytes: bytes) -> torch.Tensor:
    """Preprocesses image bytes into a normalized tensor."""
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    
    transform = transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(IMG_SIZE),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])
    
    return transform(image).unsqueeze(0) # Add batch dimension

def determine_severity(disease_name: str, confidence: float) -> int:
    """Assigns a severity level (1-5) based on prediction and confidence."""
    if disease_name == "Healthy":
        return 1 if confidence > 95 else 2 # Healthy with high confidence is low severity

    # Logic for diseased states
    if confidence < 75:
        return 2 # Low confidence, likely very early stage or mixed diagnosis
    elif confidence < 85:
        return 3 # Moderate confidence, mid-stage, local treatment recommended
    elif confidence < 95:
        return 4 # High confidence, established infection, strong treatment needed
    else:
        return 5 # Very high confidence, severe stage, requires professional consultation
    
# --- Grad-CAM Logic ---

def generate_grad_cam(model, input_tensor: torch.Tensor, predicted_index: int) -> bytes:
    """
    Generates a Grad-CAM heatmap visualization overlay.
    
    NOTE: This is a robust placeholder. Full Grad-CAM requires backpropagation hooks
    and specialized libraries (like pytorch-gradcam) to map the gradient of the
    final output back to the final convolutional layer's feature maps.
    
    For a fully functional version, you would:
    1. Register forward and backward hooks on the last convolutional layer (e.g., model.features[-1]).
    2. Zero the gradients, run model(input_tensor), and backpropagate from the predicted_index score.
    3. Compute the weighted average of feature maps using the gradients.
    4. Upsample the heatmap and overlay it on the original image.
    """
    
    # --- DUMMY GRAD-CAM FOR STRUCTURAL VALIDATION ---
    # Convert input tensor back to PIL Image for the base
    img_tensor_unnorm = input_tensor.squeeze(0) # Remove batch dimension
    mean = torch.tensor([0.485, 0.456, 0.406]).view(3, 1, 1)
    std = torch.tensor([0.229, 0.224, 0.225]).view(3, 1, 1)
    img_unnorm = (img_tensor_unnorm * std) + mean
    img_pil = transforms.ToPILImage()(img_unnorm).convert("RGB").resize((IMG_SIZE, IMG_SIZE))
    img_np = np.array(img_pil)
    
    # 1. Create a simulated red heatmap (ROI)
    heatmap = np.zeros((IMG_SIZE, IMG_SIZE, 3), dtype=np.uint8)
    
    if DISEASE_CLASSES[predicted_index] != "Healthy":
        # Simulate infection area based on index (e.g., center-right for non-healthy)
        x, y = np.random.randint(50, 100), np.random.randint(50, 100)
        heatmap[y:y+80, x:x+80, 2] = 255 # Red color in BGR format
        
    heatmap = cv2.GaussianBlur(heatmap, (15, 15), 0)
    
    # 2. Overlay the heatmap
    gradcam_image = cv2.addWeighted(cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR), 0.5, heatmap, 0.5, 0)
    
    # Convert final image back to PNG bytes
    is_success, buffer = cv2.imencode(".png", gradcam_image)
    return buffer.tobytes()

# --- Main Prediction Function ---

def predict_disease(model, image_bytes: bytes) -> dict:
    """Runs the full disease classification and Grad-CAM pipeline."""
    
    input_tensor = preprocess_image(image_bytes)
    
    with torch.no_grad():
        output = model(input_tensor)
        probabilities = F.softmax(output, dim=1)
    
    # Get top prediction
    confidences, indices = torch.topk(probabilities, 1)
    confidence = confidences.item() * 100
    predicted_index = indices.item()
    disease_name = DISEASE_CLASSES[predicted_index]
    
    # Determine severity
    severity_level = determine_severity(disease_name, confidence)

    # Generate Grad-CAM image
    gradcam_bytes = generate_grad_cam(model, input_tensor, predicted_index)
    
    # Encode Grad-CAM image to base64 for easy transfer to the frontend
    gradcam_base64 = base64.b64encode(gradcam_bytes).decode('utf-8')
    
    return {
        "disease_name": disease_name,
        "confidence": round(confidence, 2),
        "severity_level": severity_level,
        "gradcam_image": gradcam_base64 # Base64 string for display
    }