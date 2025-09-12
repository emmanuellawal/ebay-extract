#!/usr/bin/env python3
"""Create placeholder images for demo cases."""

import os
from PIL import Image, ImageDraw, ImageFont

def create_placeholder(filename, width=600, height=400, label=""):
    """Create a placeholder image with label."""
    # Create a new image with a light gray background
    img = Image.new('RGB', (width, height), color='#f0f0f0')
    draw = ImageDraw.Draw(img)
    
    # Draw a border
    draw.rectangle([(5, 5), (width-6, height-6)], outline='#888888', width=2)
    
    # Add label text
    try:
        # Try to use a default system font
        font = ImageFont.truetype("arial.ttf", 24)
    except:
        # Fallback to default font
        font = ImageFont.load_default()
    
    # Calculate text position (centered)
    bbox = draw.textbbox((0, 0), label, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    text_x = (width - text_width) // 2
    text_y = (height - text_height) // 2
    
    # Draw the text
    draw.text((text_x, text_y), label, fill='#333333', font=font)
    
    # Add filename at bottom
    filename_text = os.path.basename(filename)
    try:
        small_font = ImageFont.truetype("arial.ttf", 16)
    except:
        small_font = ImageFont.load_default()
    
    bbox = draw.textbbox((0, 0), filename_text, font=small_font)
    fname_width = bbox[2] - bbox[0]
    fname_x = (width - fname_width) // 2
    fname_y = height - 30
    
    draw.text((fname_x, fname_y), filename_text, fill='#666666', font=small_font)
    
    # Save the image
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    img.save(filename, 'JPEG', quality=85)
    print(f"Created: {filename}")

def main():
    """Create all placeholder images."""
    # Case 1: Single book
    create_placeholder(
        "products/case-001-single/img-1.jpg",
        label="D&D 2e Player's Handbook"
    )
    
    # Case 2: Multi-image iPhone
    create_placeholder(
        "products/case-002-multi-img/img-1.jpg",
        label="iPhone 13 Pro Max - Front"
    )
    create_placeholder(
        "products/case-002-multi-img/img-2.jpg",
        label="iPhone 13 Pro Max - Back"
    )
    create_placeholder(
        "products/case-002-multi-img/img-3.jpg",
        label="iPhone 13 Pro Max - Side"
    )
    
    # Case 3: Multi-product lot
    create_placeholder(
        "products/case-003-multi-product/photo.jpg",
        label="Three Small Items"
    )
    
    print("\nAll placeholder images created successfully!")

if __name__ == "__main__":
    main()
