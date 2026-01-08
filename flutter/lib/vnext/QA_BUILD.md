# QA APK Build Instructions

## Build with QA Environment

### Option 1: Using API_ENV build-define
```bash
# Build APK for QA environment
flutter build apk --debug --dart-define=API_ENV=qa

# Build APK with custom VNEXT_API_BASE
flutter build apk --debug \
  --dart-define=API_ENV=qa \
  --dart-define=VNEXT_API_BASE=https://qa-api.afkzone.cloud
```

### Option 2: Using full URL override
```bash
flutter build apk --debug \
  --dart-define=VNEXT_API_BASE=https://your-qa-server.com
```

### Option 3: Dev mode (hot reload)
```bash
flutter run --dart-define=API_ENV=qa
```

---

## APK Output Location
```
flutter/build/app/outputs/flutter-apk/app-debug.apk
```

---

## Environment Values

| API_ENV | Base URL |
|---------|----------|
| production | https://api.afkzone.cloud |
| staging | https://staging-api.afkzone.cloud |
| qa | VNEXT_API_BASE (default: https://qa-api.afkzone.cloud) |
| local | http://localhost:8000 |

---

## Verify Environment in App
When app starts, check logs for:
```
[ConfigService] [timestamp] Loading config from https://qa-api.afkzone.cloud/public/mobile-ui-config
```

---

## For OpusC QA Testing

### Prerequisites
1. Opus backend must be running at VNEXT_API_BASE
2. GET /public/mobile-ui-config must return signed envelope

### Build Command (Copy & Run)
```bash
cd flutter
flutter build apk --debug --dart-define=API_ENV=qa
```

### APK Location
```
D:\rustdesk-dev\flutter\build\app\outputs\flutter-apk\app-debug.apk
```
