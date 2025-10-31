#!/bin/bash
# Create simple 1x1 pixel placeholder images using base64

# 1x1 green pixel PNG
echo -n "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==" | base64 -d > logo.png

# Create slightly larger placeholders (10x10 green)
python3 << 'PYTHON'
import struct
import zlib

def create_png(width, height, r, g, b, filename):
    """Create a simple solid-color PNG"""
    # PNG signature
    png_data = b'\x89PNG\r\n\x1a\n'
    
    # IHDR chunk
    ihdr_data = struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)
    ihdr_crc = zlib.crc32(b'IHDR' + ihdr_data) & 0xffffffff
    png_data += struct.pack('>I', 13) + b'IHDR' + ihdr_data + struct.pack('>I', ihdr_crc)
    
    # IDAT chunk (image data)
    idat_raw = b''
    for _ in range(height):
        idat_raw += b'\x00' + bytes([r, g, b]) * width
    
    idat_data = zlib.compress(idat_raw)
    idat_crc = zlib.crc32(b'IDAT' + idat_data) & 0xffffffff
    png_data += struct.pack('>I', len(idat_data)) + b'IDAT' + idat_data + struct.pack('>I', idat_crc)
    
    # IEND chunk
    iend_crc = zlib.crc32(b'IEND') & 0xffffffff
    png_data += struct.pack('>I', 0) + b'IEND' + struct.pack('>I', iend_crc)
    
    with open(f'/workspace/cmhf3eeab02iptmik204h7jw9/SmartCropDoc-AI/frontend/images/{filename}', 'wb') as f:
        f.write(png_data)
    print(f"Created {filename}")

# Create placeholder images
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
PYTHON
