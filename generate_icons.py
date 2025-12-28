#!/usr/bin/env python3
"""
Generate all Android launcher icons from the new AFK Zone logo
"""

from PIL import Image
import os

# Source logo
source_logo = "NewAFKZoneLogo.png"

# Android icon sizes (launcher icons)
icon_sizes = {
    "mipmap-mdpi": 48,
    "mipmap-hdpi": 72,
    "mipmap-xhdpi": 96,
    "mipmap-xxhdpi": 144,
    "mipmap-xxxhdpi": 192,
}

# Foreground icon sizes (adaptive icons)
foreground_sizes = {
    "mipmap-mdpi": 108,
    "mipmap-hdpi": 162,
    "mipmap-xhdpi": 216,
    "mipmap-xxhdpi": 324,
    "mipmap-xxxhdpi": 432,
}

def resize_image(input_path, output_path, size):
    """Resize image to specified size with high quality"""
    img = Image.open(input_path)
    
    # Convert to RGBA if not already
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    
    # Resize with high-quality resampling
    img_resized = img.resize((size, size), Image.Resampling.LANCZOS)
    
    # Save
    img_resized.save(output_path, 'PNG', optimize=True)
    print(f"[OK] Created: {output_path} ({size}x{size})")

def main():
    print("=" * 60)
    print("AFK ZONE - ICON GENERATOR")
    print("=" * 60)
    print()
    
    if not os.path.exists(source_logo):
        print(f"❌ Error: {source_logo} not found!")
        return
    
    base_path = "flutter/android/app/src/main/res"
    
    # Generate launcher icons
    print("Generating launcher icons...")
    for folder, size in icon_sizes.items():
        output_dir = os.path.join(base_path, folder)
        os.makedirs(output_dir, exist_ok=True)
        
        # ic_launcher.png
        output_file = os.path.join(output_dir, "ic_launcher.png")
        resize_image(source_logo, output_file, size)
        
        # ic_launcher_round.png (same as regular for now)
        output_file_round = os.path.join(output_dir, "ic_launcher_round.png")
        resize_image(source_logo, output_file_round, size)
    
    print()
    print("Generating foreground icons (adaptive)...")
    for folder, size in foreground_sizes.items():
        output_dir = os.path.join(base_path, folder)
        os.makedirs(output_dir, exist_ok=True)
        
        # ic_launcher_foreground.png
        output_file = os.path.join(output_dir, "ic_launcher_foreground.png")
        resize_image(source_logo, output_file, size)
    
    print()
    print("Generating notification icon...")
    # Notification icon (small, monochrome-style but we'll use colored for now)
    notification_dir = os.path.join(base_path, "mipmap-xxhdpi")
    notification_file = os.path.join(notification_dir, "ic_stat_logo.png")
    resize_image(source_logo, notification_file, 72)
    
    print()
    print("=" * 60)
    print("ALL ICONS GENERATED SUCCESSFULLY!")
    print("=" * 60)

if __name__ == "__main__":
    main()

