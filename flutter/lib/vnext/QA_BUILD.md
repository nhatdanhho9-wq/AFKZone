# QA APK Build Instructions

## Build with QA Environment

## Prerequisite (Android/Gradle)

This project requires **JDK 17+** for Android builds (AGP 8.x). If Gradle runs on Java 8/11, you will see errors like:

- `No matching variant ... compatible with Java 8`
- `Unsupported class file major version ...`

On Windows PowerShell, set `JAVA_HOME` to JDK 17+ before building.

### Option 1: Using API_ENV build-define
```bash
# Build APK for QA environment
AFK_VNEXT_ONLY=1 flutter build apk --debug -t lib/vnext/main_vnext.dart --dart-define=API_ENV=qa

# Build APK with custom VNEXT_API_BASE
AFK_VNEXT_ONLY=1 flutter build apk --debug -t lib/vnext/main_vnext.dart \
  --dart-define=API_ENV=qa \
  --dart-define=VNEXT_API_BASE=https://qa-api.afkzone.cloud
```

### Option 2: Using full URL override
```bash
AFK_VNEXT_ONLY=1 flutter build apk --debug -t lib/vnext/main_vnext.dart \
  --dart-define=VNEXT_API_BASE=https://your-qa-server.com
```

### Option 3: Dev mode (hot reload)
```bash
AFK_VNEXT_ONLY=1 flutter run -t lib/vnext/main_vnext.dart --dart-define=API_ENV=qa
```

---

## Windows PowerShell (Copy/Paste)

```powershell
$env:AFK_VNEXT_ONLY="1"
$env:JAVA_HOME="C:\\Program Files\\Java\\jdk-21"   # or jdk-17
$env:Path="$env:JAVA_HOME\\bin;$env:Path"

cd D:\rustdesk-dev\flutter
flutter build apk --debug -t lib/vnext/main_vnext.dart `
  --dart-define=API_ENV=qa `
  --dart-define=VNEXT_API_BASE=http://172.26.31.115:21121
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
AFK_VNEXT_ONLY=1 flutter build apk --debug -t lib/vnext/main_vnext.dart --dart-define=API_ENV=qa
```

### APK Location
```
D:\rustdesk-dev\flutter\build\app\outputs\flutter-apk\app-debug.apk
```
