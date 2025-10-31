#!/bin/bash

# CropGuard AI - Complete Setup Script
# This script sets up the entire project for running

set -e

echo "=========================================="
echo "CropGuard AI - Setup Script"
echo "=========================================="
echo ""

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

# Step 1: Check Python version
echo "Step 1: Checking Python version..."
PYTHON_VERSION=$(python3 --version | awk '{print $2}')
print_status "Python $PYTHON_VERSION found"

# Step 2: Install core dependencies
echo ""
echo "Step 2: Installing core dependencies..."
pip install -q Flask Flask-CORS python-dotenv requests Werkzeug
print_status "Core dependencies installed"

# Step 3: Install ML dependencies (optional, but helpful)
echo ""
echo "Step 3: Installing optional ML dependencies..."
echo "Note: This may take several minutes..."
pip install -q Pillow numpy opencv-python 2>/dev/null || print_warning "Some ML dependencies may need additional setup"
print_status "ML dependencies installed"

# Step 4: Create .env if it doesn't exist
echo ""
echo "Step 4: Verifying .env configuration..."
if [ -f ".env" ]; then
    print_status ".env file exists"
else
    print_warning ".env file not found, creating one..."
    cat > .env << 'ENVEOF'
GROQ_API_KEY=gsk_your_groq_api_key_here
LLM_PROVIDER_NAME=Groq
FLASK_ENV=development
DEBUG=True
FLASK_APP=app/main.py
MODEL_WEIGHTS_PATH=models/mobilenetv3_best.pth
ENHANCER_MODEL_PATH=models/enhancer_weights/RealESRGAN_x4plus.pth
HOST=0.0.0.0
PORT=5000
SECRET_KEY=cropguard-dev-secret-key-change-in-production-2025
LOG_LEVEL=INFO
ENVEOF
    print_status ".env file created"
fi

# Step 5: Check directories
echo ""
echo "Step 5: Checking required directories..."
mkdir -p frontend/images
mkdir -p models/enhancer_weights
print_status "Directories verified"

# Step 6: Check for placeholder images
echo ""
echo "Step 6: Verifying placeholder images..."
if [ -f "frontend/images/logo.png" ]; then
    print_status "Placeholder images found"
else
    print_warning "Creating placeholder images..."
    cd frontend/images
    python3 << 'PYEOF'
import struct
import zlib

def create_png(width, height, r, g, b, filename):
    png_data = b'\x89PNG\r\n\x1a\n'
    ihdr_data = struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)
    ihdr_crc = zlib.crc32(b'IHDR' + ihdr_data) & 0xffffffff
    png_data += struct.pack('>I', 13) + b'IHDR' + ihdr_data + struct.pack('>I', ihdr_crc)
    idat_raw = b''
    for _ in range(height):
        idat_raw += b'\x00' + bytes([r, g, b]) * width
    idat_data = zlib.compress(idat_raw)
    idat_crc = zlib.crc32(b'IDAT' + idat_data) & 0xffffffff
    png_data += struct.pack('>I', len(idat_data)) + b'IDAT' + idat_data + struct.pack('>I', idat_crc)
    iend_crc = zlib.crc32(b'IEND') & 0xffffffff
    png_data += struct.pack('>I', 0) + b'IEND' + struct.pack('>I', iend_crc)
    with open(filename, 'wb') as f:
        f.write(png_data)

create_png(100, 100, 76, 175, 80, 'logo.png')
create_png(300, 300, 220, 50, 50, 'apple.jpg')
create_png(300, 300, 255, 140, 0, 'mango.jpg')
create_png(300, 300, 255, 200, 50, 'banana.jpg')
create_png(300, 300, 180, 82, 205, 'grapes.jpg')
create_png(300, 300, 165, 105, 80, 'potato.jpg')
create_png(300, 300, 220, 50, 50, 'tomato.jpg')
create_png(300, 300, 144, 238, 144, 'cauliflower.jpg')
create_png(300, 300, 255, 215, 0, 'corn.jpg')
create_png(600, 400, 76, 175, 80, 'about.jpg')
create_png(1200, 600, 76, 175, 80, 'guidebg.png')
PYEOF
    cd ../..
    print_status "Placeholder images created"
fi

# Step 7: Summary
echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Update .env file with your Groq API key:"
echo "   GROQ_API_KEY=gsk_your_actual_api_key"
echo ""
echo "2. Run the Flask application:"
echo "   python app/main.py"
echo ""
echo "3. Access the web interface:"
echo "   http://localhost:5000"
echo ""
echo "4. To use the full ML features, install additional dependencies:"
echo "   pip install torch torchvision realesrgan basicsr"
echo ""
