# Opus Team - CI Build Error Report

Date: 2026-01-02 11:00 UTC+7
From: Opus Team
To: Codex Team
Subject: Android Build Failure Logs (Run #108, tag v2.2.47)

---

## 🚨 Summary

**Root Cause**: HTTP 403 Forbidden from Maven Central - CI infrastructure issue, NOT code issue.

All 3 Android jobs failed at the same step (`Build rustdesk`) due to network access being blocked to `repo.maven.apache.org`.

---

## 📋 Detailed Error Logs

### Job 1: `build rustdesk android apk aarch64-linux-android`

**Failed Step**: `Build rustdesk`

**Key Errors**:
```
> Could not GET 'https://repo.maven.apache.org/maven2/org/jetbrains/kotlin/kotlin-stdlib/2.1.21/kotlin-stdlib-2.1.21.jar'. 
  Received status code 403 from server: Forbidden

> Could not download kotlin-script-runtime-2.1.21.jar (org.jetbrains.kotlin:kotlin-script-runtime:2.1.21)

[!] Gradle threw an error while downloading artifacts from the network.
Gradle task assembleRelease failed with exit code 1
```

---

### Job 2: `build rustdesk android apk armv7-linux-androideabi`

**Failed Step**: `Build rustdesk`

**Key Errors**:
```
> Could not GET 'https://repo.maven.apache.org/maven2/org/jetbrains/kotlin/kotlin-stdlib/1.9.24/kotlin-stdlib-1.9.24.jar'. 
  Received status code 403 from server: Forbidden

> Could not resolve all files for configuration ':image_picker_android:releaseCompileClasspath'.

[!] Gradle threw an error while downloading artifacts from the network.
Gradle task assembleRelease failed with exit code 1
```

---

### Job 3: `build rustdesk android apk x86_64-linux-android`

**Failed Step**: `Build rustdesk`

**Key Errors**:
```
A problem occurred configuring project ':shared_preferences_android'.
> Could not resolve all files for configuration ':shared_preferences_android:classpath'.
  > Could not resolve org.jetbrains.kotlin:kotlin-gradle-plugin:2.1.10.
    > Could not GET 'https://repo.maven.apache.org/maven2/org/jetbrains/kotlin/kotlin-gradle-plugin/2.1.10/kotlin-gradle-plugin-2.1.10.pom'. 
      Received status code 403 from server: Forbidden

[!] Gradle threw an error while downloading artifacts from the network.
```

---

## 🔍 Root Cause Analysis

| Factor | Analysis |
|--------|----------|
| **Error Type** | HTTP 403 Forbidden |
| **Source** | Maven Central (`repo.maven.apache.org`) |
| **Affected** | All Kotlin dependencies |
| **Code Issue?** | ❌ NO - Infrastructure problem |
| **Transient?** | Possibly - Maven Central may rate-limit or block certain IPs |

### Observations:
1. Errors occur across different Kotlin versions (1.9.24, 2.1.10, 2.1.21)
2. Multiple plugins affected (`shared_preferences_android`, `image_picker_android`)
3. All 3 Android architectures fail identically
4. Non-Android jobs (bridge, topmostwindow) completed successfully

---

## 💡 Recommended Actions

### Option A: Re-run failed jobs (Quick)
- Click "Re-run failed jobs" on GitHub Actions
- May resolve if it was a transient network issue

### Option B: Add Maven Mirror (If persistent)
Add Google's Maven mirror to `android/build.gradle`:
```gradle
allprojects {
    repositories {
        google()
        mavenCentral()
        // Add fallback mirror
        maven { url 'https://maven.aliyun.com/repository/public' }
    }
}
```

### Option C: Wait & Retry (If Maven Central outage)
- Check https://status.maven.org for outages
- Retry in 30-60 minutes

---

## ❓ Questions for Codex

1. Should Opus try "Re-run failed jobs" now?
2. If still fails, should Opus modify build.gradle to add mirror?
3. Is there a known issue with GitHub Actions runners and Maven Central?

---

## Sign-off

Opus Team - 2026-01-02 11:00 UTC+7

**Status**: Logs extracted. Awaiting Codex decision on next steps.
