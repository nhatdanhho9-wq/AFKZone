# Phase 4b Client Build - Blocker Report

Date: 2026-01-01
Owner: Codex Team
Audience: Opus Team

## What was attempted
1) `flutter pub get`
2) `flutter build apk --debug`

## Result
Build failed with:
```
Unsupported class file major version 65
Gradle 7.6.4 is not compatible with Java 21
```

## Root Cause
- Flutter is using Java 21 (Android Studio JBR).
- Gradle wrapper is 7.6.4 and AGP is 7.3.1.
- Gradle 7.6.x does not support Java 21.

## Fix Options

### Option A (fast, no repo changes)
Use JDK 17 for builds.
- Install JDK 17 (Temurin/Adoptium).
- Set:
  - `JAVA_HOME=<JDK17_PATH>`
  - `flutter config --jdk-dir <JDK17_PATH>`
- Rebuild:
  - `flutter build apk --debug`

### Option B (permanent, repo changes)
Upgrade Gradle + Android Gradle Plugin to support Java 21.
1) `android/gradle/wrapper/gradle-wrapper.properties`
   - `distributionUrl=https://services.gradle.org/distributions/gradle-8.7-all.zip`
2) `android/settings.gradle`
   - `com.android.application` → `8.5.2`
3) `android/app/build.gradle`
   - Add `namespace "com.afkzone.remote"` under `android { }`
   - Keep `compileSdkVersion 34` (or update to 35 if required by AGP)
4) Rebuild:
   - `flutter build apk --debug`

## Recommendation
- Use Option A to finish verification quickly.
- Schedule Option B in Phase 5 (build system cleanup).

## Sign-off
Codex Team - 2026-01-01
