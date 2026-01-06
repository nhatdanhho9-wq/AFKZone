"""
Generate macOS .icns with full sizes including 1024 (as ic10)
"""
from PIL import Image
import icnsutil
import os

SOURCE = r"D:\rustdesk-dev\AFKzonelogo.png"
ICNS_OUTPUT = r"D:\rustdesk-dev\flutter\macos\Runner\Assets.xcassets\AppIcon.appiconset\app_icon.icns"
ICNS_LEGACY = r"D:\rustdesk-dev\flutter\macos\Runner\AppIcon.icns"

def resize_with_padding(img, target_size, padding_ratio=0.1):
    inner_size = int(target_size * (1 - padding_ratio * 2))
    img_resized = img.copy()
    img_resized.thumbnail((inner_size, inner_size), Image.LANCZOS)
    result = Image.new('RGBA', (target_size, target_size), (255, 255, 255, 0))
    offset = ((target_size - img_resized.width) // 2, (target_size - img_resized.height) // 2)
    result.paste(img_resized, offset, img_resized if img_resized.mode == 'RGBA' else None)
    return result

# Load source
print(f"Loading: {SOURCE}")
source_img = Image.open(SOURCE).convert('RGBA')
print(f"Source size: {source_img.width}x{source_img.height}")

# All standard macOS icns sizes
# Standard: 16, 32, 128, 256, 512
# Retina (@2x): 32 (16@2x), 64 (32@2x), 256 (128@2x), 512 (256@2x), 1024 (512@2x)
icns_sizes = [16, 32, 64, 128, 256, 512, 1024]

print("\nGenerating .icns file with all sizes...")
icns = icnsutil.IcnsFile()

added_sizes = []
for size in icns_sizes:
    resized = resize_with_padding(source_img, size)
    temp_path = f"temp_icon_{size}.png"
    resized.save(temp_path, 'PNG')
    
    try:
        icns.add_media(file=temp_path)
        print(f"  ✅ Added: {size}x{size}")
        added_sizes.append(size)
    except Exception as e:
        print(f"  ⚠️ Skipped {size}x{size}: {str(e)[:50]}")
    
    os.remove(temp_path)

# Save icns
os.makedirs(os.path.dirname(ICNS_OUTPUT), exist_ok=True)
icns.write(ICNS_OUTPUT)
print(f"\n✅ Created: {ICNS_OUTPUT}")

# Copy to legacy location
import shutil
shutil.copy(ICNS_OUTPUT, ICNS_LEGACY)
print(f"✅ Copied to: {ICNS_LEGACY}")

# Get file size
file_size = os.path.getsize(ICNS_OUTPUT)
print(f"\nFile size: {file_size} bytes ({file_size // 1024} KB)")
print(f"\nSizes included: {added_sizes}")

# List icns contents
print("\n=== ICNS Media Contents ===")
for entry in icns.media:
    print(f"  {entry}")
