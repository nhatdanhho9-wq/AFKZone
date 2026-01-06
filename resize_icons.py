"""
Icon Resize Script for AFK Zone v2.2.56
Source: D:\rustdesk-dev\AFKzonelogo.png
"""
from PIL import Image
import os

# Source logo
SOURCE = r"D:\rustdesk-dev\AFKzonelogo.png"
FLUTTER_DIR = r"D:\rustdesk-dev\flutter"

def resize_with_padding(img, target_size, padding_ratio=0.1):
    """Resize image with padding to avoid cutting text"""
    # Calculate padded size (image will be smaller to add padding)
    inner_size = int(target_size * (1 - padding_ratio * 2))
    
    # Resize maintaining aspect ratio
    img_resized = img.copy()
    img_resized.thumbnail((inner_size, inner_size), Image.LANCZOS)
    
    # Create new image with padding
    result = Image.new('RGBA', (target_size, target_size), (255, 255, 255, 0))
    
    # Center the resized image
    offset = ((target_size - img_resized.width) // 2, (target_size - img_resized.height) // 2)
    result.paste(img_resized, offset, img_resized if img_resized.mode == 'RGBA' else None)
    
    return result

def save_png(img, path, size):
    """Save as PNG with correct size"""
    resized = resize_with_padding(img, size)
    resized.save(path, 'PNG')
    print(f"  ✅ {os.path.basename(path)}: {size}x{size}")

def save_ico(img, path, sizes):
    """Save as ICO with multiple sizes"""
    icons = [resize_with_padding(img, s) for s in sizes]
    icons[0].save(path, format='ICO', sizes=[(s, s) for s in sizes])
    print(f"  ✅ {os.path.basename(path)}: multi-size ICO")

# Load source image
print(f"Loading source: {SOURCE}")
source_img = Image.open(SOURCE).convert('RGBA')
print(f"Source size: {source_img.width}x{source_img.height}")

# ==== ANDROID LAUNCHER ====
print("\n=== Android Launcher Icons ===")
android_sizes = {
    'mipmap-mdpi': 48,
    'mipmap-hdpi': 72,
    'mipmap-xhdpi': 96,
    'mipmap-xxhdpi': 144,
    'mipmap-xxxhdpi': 192,
}

for folder, size in android_sizes.items():
    base_path = os.path.join(FLUTTER_DIR, 'android', 'app', 'src', 'main', 'res', folder)
    
    # ic_launcher.png
    save_png(source_img, os.path.join(base_path, 'ic_launcher.png'), size)
    
    # ic_launcher_round.png
    save_png(source_img, os.path.join(base_path, 'ic_launcher_round.png'), size)
    
    # ic_launcher_foreground.png (slightly larger for adaptive icon)
    save_png(source_img, os.path.join(base_path, 'ic_launcher_foreground.png'), size)
    
    # ic_stat_logo.png (notification)
    save_png(source_img, os.path.join(base_path, 'ic_stat_logo.png'), size)

# ==== iOS AppIcon ====
print("\n=== iOS AppIcon ===")
ios_path = os.path.join(FLUTTER_DIR, 'ios', 'Runner', 'Assets.xcassets', 'AppIcon.appiconset')

ios_icons = [
    ('Icon-App-20x20@1x.png', 20),
    ('Icon-App-20x20@2x.png', 40),
    ('Icon-App-20x20@3x.png', 60),
    ('Icon-App-29x29@1x.png', 29),
    ('Icon-App-29x29@2x.png', 58),
    ('Icon-App-29x29@3x.png', 87),
    ('Icon-App-40x40@1x.png', 40),
    ('Icon-App-40x40@2x.png', 80),
    ('Icon-App-40x40@3x.png', 120),
    ('Icon-App-60x60@2x.png', 120),
    ('Icon-App-60x60@3x.png', 180),
    ('Icon-App-76x76@1x.png', 76),
    ('Icon-App-76x76@2x.png', 152),
    ('Icon-App-83.5x83.5@2x.png', 167),
    ('Icon-App-1024x1024@1x.png', 1024),
]

for filename, size in ios_icons:
    save_png(source_img, os.path.join(ios_path, filename), size)

# ==== Flutter Assets ====
print("\n=== Flutter Assets ===")
assets_path = os.path.join(FLUTTER_DIR, 'assets')
save_png(source_img, os.path.join(assets_path, 'logo.png'), 512)
save_png(source_img, os.path.join(assets_path, 'afkzone_logo.png'), 512)

# ==== Windows ICO ====
print("\n=== Windows ===")
win_path = os.path.join(FLUTTER_DIR, 'windows', 'runner', 'resources')
ico_sizes = [16, 32, 48, 64, 128, 256]
save_ico(source_img, os.path.join(win_path, 'app_icon.ico'), ico_sizes)

# Also save PNG for reference
save_png(source_img, os.path.join(win_path, 'app_icon.png'), 256)

# ==== macOS ====
print("\n=== macOS ===")
macos_path = os.path.join(FLUTTER_DIR, 'macos', 'Runner')
# For macOS, save as PNG (icns needs special tool)
save_png(source_img, os.path.join(macos_path, 'AppIcon.png'), 1024)

print("\n✅ All icons resized successfully!")
print("\nNote: macOS .icns file needs to be generated using iconutil tool on macOS")
