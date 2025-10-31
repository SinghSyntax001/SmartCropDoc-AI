#!/usr/bin/env python3
"""Create placeholder images for CropGuard AI"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_placeholder(name, text, width=300, height=300, color=(76, 175, 80)):
    """Create a placeholder image"""
    img = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(img)
    
    # Draw colored rectangle
    draw.rectangle([(0, 0), (width, height)], fill=color)
    
    # Draw text
    try:
        # Try to use a default font
        font_size = int(width / 8)
        draw.text((width//2, height//2), text, fill='white', anchor='mm')
    except:
        pass
    
    # Save the image
    path = f'/workspace/cmhf3eeab02iptmik204h7jw9/SmartCropDoc-AI/frontend/images/{name}.jpg'
    img.save(path, 'JPEG', quality=85)
    print(f"Created {path}")

# Create placeholder images
images = [
    ('logo', '🌱', 200, 200, (76, 175, 80)),
    ('apple', 'Apple', 300, 300, (220, 50, 50)),
    ('mango', 'Mango', 300, 300, (255, 140, 0)),
    ('banana', 'Banana', 300, 300, (255, 255, 0)),
    ('grapes', 'Grapes', 300, 300, (180, 82, 205)),
    ('potato', 'Potato', 300, 300, (165, 105, 80)),
    ('tomato', 'Tomato', 300, 300, (220, 50, 50)),
    ('cauliflower', 'Cauliflower', 300, 300, (144, 238, 144)),
    ('corn', 'Corn', 300, 300, (255, 215, 0)),
    ('about', 'CropGuard Team', 600, 400, (76, 175, 80)),
    ('guidebg', 'Guide', 1200, 600, (76, 175, 80)),
]

for name, text, w, h, color in images:
    create_placeholder(name, text, w, h, color)

print("All placeholder images created!")
