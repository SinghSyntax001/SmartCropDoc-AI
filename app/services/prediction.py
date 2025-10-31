import torch
import torch.nn as nn
from torchvision import models, transforms
from PIL import Image
import os

# ==========================================================
# CONFIG
# ==========================================================
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

DISEASE_CLASSES = [
    "Apple_Black_rot", "Apple_scab", "Banana_Panama", "Cauliflower_Black_Rot",
    "Corn_(maize)_Cercospora_leaf_spot", "Corn_(maize)_Northern_Leaf_Blight",
    "Grape_healthy", "Mango_Gall_Midge", "Potato_Early_blight", "Tomato_Bacterial_spot",
    "Tomato_Two_spotted_Spider_mites", "Apple_Cedar_apple_rust", "Banana_Fusarium_wilt",
    "Banana_Sigatoka", "Cauliflower_Downy_Mildew", "Corn_(maize)_Common_rust",
    "Grape_Black_rot", "Grape_Leaf_blight_(Isariopsis_Leaf_Spot)", "Mango_Healthy",
    "Potato_healthy", "Tomato_Early_blight", "Apple_healthy", "Banana_Healthy",
    "Cauliflower_Bacterial_spot_rot", "Cauliflower_Healthy", "Corn_(maize)_healthy",
    "Grape_Esca_(Black_Measles)", "Mango_Anthracnose", "Mango_Powdery Mildew",
    "Potato_Late_blight", "Tomato_healthy"
]

# ==========================================================
# MODEL LOADING
# ==========================================================
def load_mobilenet_model(weights_path: str):
    """
    Load MobileNetV3-Large model with trained weights.
    Compatible with Flask import: app.services.prediction.load_mobilenet_model
    """
    model = models.mobilenet_v3_large(pretrained=False)
    num_ftrs = model.classifier[3].in_features
    model.classifier[3] = nn.Linear(num_ftrs, len(DISEASE_CLASSES))

    if not os.path.exists(weights_path):
        raise FileNotFoundError(f"❌ Model weights not found at: {weights_path}")

    model.load_state_dict(torch.load(weights_path, map_location=DEVICE))
    model.to(DEVICE)
    model.eval()
    print(f"✅ MobileNetV3 model loaded successfully from {weights_path}")
    return model

# ==========================================================
# IMAGE PREPROCESSING
# ==========================================================
def preprocess_image(image_path: str):
    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406],
                             std=[0.229, 0.224, 0.225])
    ])
    image = Image.open(image_path).convert("RGB")
    return transform(image).unsqueeze(0)

# ==========================================================
# PREDICTION FUNCTION
# ==========================================================
def predict_disease(model, image_path: str):
    """Run inference and return predicted class + confidence."""
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"❌ Image not found: {image_path}")

    image_tensor = preprocess_image(image_path).to(DEVICE)

    with torch.no_grad():
        outputs = model(image_tensor)
        probabilities = torch.softmax(outputs, dim=1)
        confidence, pred_idx = torch.max(probabilities, 1)

    pred_class = DISEASE_CLASSES[pred_idx.item()]
    confidence = round(confidence.item() * 100, 2)

    return {"prediction": pred_class, "confidence": confidence}
