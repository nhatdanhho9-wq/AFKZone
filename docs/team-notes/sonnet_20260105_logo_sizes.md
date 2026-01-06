From: Sonnet Team
To: Codex Team
Date: 2026-01-05
Subject: ICON SIZE MATRIX - Properly Resized Icons

Status: ICONS PROPERLY SIZED ✅

## Commit

76d6a3acb - 40 files properly resized

## Source

- File: D:\rustdesk-dev\AFKzonelogo.png
- Original Size: 2048x2048 pixels
- Tool: Python Pillow with LANCZOS resampling
- Padding: 10% safe padding (no text cut)

## A) Android Launcher Icons ✅

| Density | Size | ic_launcher | ic_launcher_round | ic_launcher_foreground |
|---------|------|-------------|-------------------|------------------------|
| mdpi | 48x48 | ✅ | ✅ | ✅ |
| hdpi | 72x72 | ✅ | ✅ | ✅ |
| xhdpi | 96x96 | ✅ | ✅ | ✅ |
| xxhdpi | 144x144 | ✅ | ✅ | ✅ |
| xxxhdpi | 192x192 | ✅ | ✅ | ✅ |

Path: flutter/android/app/src/main/res/mipmap-*/

## B) Android Notification Icons ✅

| Density | Size | ic_stat_logo |
|---------|------|--------------|
| mdpi | 48x48 | ✅ |
| hdpi | 72x72 | ✅ |
| xhdpi | 96x96 | ✅ |
| xxhdpi | 144x144 | ✅ |
| xxxhdpi | 192x192 | ✅ |

Path: flutter/android/app/src/main/res/mipmap-*/

## C) iOS AppIcon ✅

| File | Size (px) | Status |
|------|-----------|--------|
| Icon-App-20x20@1x.png | 20x20 | ✅ |
| Icon-App-20x20@2x.png | 40x40 | ✅ |
| Icon-App-20x20@3x.png | 60x60 | ✅ |
| Icon-App-29x29@1x.png | 29x29 | ✅ |
| Icon-App-29x29@2x.png | 58x58 | ✅ |
| Icon-App-29x29@3x.png | 87x87 | ✅ |
| Icon-App-40x40@1x.png | 40x40 | ✅ |
| Icon-App-40x40@2x.png | 80x80 | ✅ |
| Icon-App-40x40@3x.png | 120x120 | ✅ |
| Icon-App-60x60@2x.png | 120x120 | ✅ |
| Icon-App-60x60@3x.png | 180x180 | ✅ |
| Icon-App-76x76@1x.png | 76x76 | ✅ |
| Icon-App-76x76@2x.png | 152x152 | ✅ |
| Icon-App-83.5x83.5@2x.png | 167x167 | ✅ |
| Icon-App-1024x1024@1x.png | 1024x1024 | ✅ |

Path: flutter/ios/Runner/Assets.xcassets/AppIcon.appiconset/

## D) Windows ✅

| File | Sizes | Status |
|------|-------|--------|
| app_icon.ico | 16,32,48,64,128,256 | ✅ Multi-size ICO |
| app_icon.png | 256x256 | ✅ |

Path: flutter/windows/runner/resources/

## E) macOS ✅

| File | Size | Status |
|------|------|--------|
| AppIcon.png | 1024x1024 | ✅ |

Path: flutter/macos/Runner/
Note: .icns needs iconutil on macOS to generate from PNG

## Flutter Assets ✅

| File | Size | Status |
|------|------|--------|
| logo.png | 512x512 | ✅ |
| afkzone_logo.png | 512x512 | ✅ |

Path: flutter/assets/

## Summary

| Platform | Files | Status |
|----------|-------|--------|
| Android Launcher | 15 | ✅ Correct sizes |
| Android Notification | 5 | ✅ Correct sizes |
| iOS AppIcon | 15 | ✅ Apple sizes |
| Windows | 2 | ✅ Multi-size ICO |
| macOS | 1 | ✅ 1024px PNG |
| Flutter Assets | 2 | ✅ 512px |
| **Total** | **40** | ✅ |

## Technical Details

- Resize method: Pillow Image.thumbnail() with LANCZOS
- Padding: 10% on each side (image = 80% of canvas)
- Format: PNG with RGBA (transparency preserved)
- No text cutting: Safe padding ensures "AFK" text visible

## Evidence

- Commit: 76d6a3acb
- GitHub: https://github.com/nhatdanhho9-wq/AFKZone/commit/76d6a3acb
- Resize script: D:\rustdesk-dev\resize_icons.py

## Screenshots

⚠️ Device screenshots require building and deploying APK/IPA.
Request: After CI build completes, please test on device and capture home screen icon.
