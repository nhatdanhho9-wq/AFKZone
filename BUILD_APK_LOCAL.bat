@echo off
REM ========================================
REM BUILD APK LOCAL - AFK ZONE v2.2.1
REM ========================================

echo.
echo ========================================
echo  Building AFK Zone APK locally...
echo ========================================
echo.

cd /d D:\rustdesk-dev\flutter

echo [1/5] Cleaning Flutter cache...
flutter clean

echo.
echo [2/5] Getting dependencies...
flutter pub get

echo.
echo [3/5] Analyzing code...
flutter analyze

echo.
echo [4/5] Building APK (Release mode)...
flutter build apk --release --target-platform android-arm64

echo.
echo [5/5] Locating APK...
echo.
echo ========================================
echo  BUILD COMPLETE!
echo ========================================
echo.
echo APK location:
echo D:\rustdesk-dev\flutter\build\app\outputs\flutter-apk\app-arm64-v8a-release.apk
echo.
echo To install:
echo 1. Connect Android device
echo 2. Run: adb install build\app\outputs\flutter-apk\app-arm64-v8a-release.apk
echo.
pause
