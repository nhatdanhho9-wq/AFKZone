From: Opus Team  
To: Codex Team  
Date: 2026-01-06  
Subject: CI Fix - Android Maven 403 (osdetector-gradle-plugin) ✅

---

## Root Cause

**Error:**
```
Could not download osdetector-gradle-plugin-1.7.3.jar
403 Forbidden from Maven Central
```

**Cause:** `osdetector-gradle-plugin` is a transitive dependency of `com.google.protobuf:protobuf-gradle-plugin:0.9.4` (flutter/android/app/build.gradle line 5). Maven Central intermittently returns 403 for this artifact.

---

## Fix Applied

**Commit:** de3962100  
**File:** `flutter/android/app/build.gradle`

### Changes
```diff
repositories {
    ...
    google()
    mavenCentral()
+   gradlePluginPortal()  // Required for osdetector-gradle-plugin
    maven { url 'https://repo1.maven.org/maven2' }
    maven { url 'https://jitpack.io' }
+   // Fallback mirrors for CI reliability (Maven Central 403 workaround)
+   maven { url 'https://plugins.gradle.org/m2/' }
+   maven { url 'https://maven.aliyun.com/repository/public' }
+   maven { url 'https://maven.aliyun.com/repository/gradle-plugin' }
}
```

### Fallback Chain
1. `gradlePluginPortal()` - Official Gradle plugin mirror
2. `plugins.gradle.org/m2/` - Direct URL fallback
3. `maven.aliyun.com` mirrors - China CDN fallback

---

## Dependencies

| Dependency | Source |
|------------|--------|
| com.google.protobuf:0.9.4 | Uses osdetector-gradle-plugin:1.7.3 |
| osdetector-gradle-plugin:1.7.3 | Available on Gradle Plugin Portal |

---

## Verification

Next CI build should show:
```
> Task :app:preBuild
osdetector-gradle-plugin:1.7.3 resolved from plugins.gradle.org
```

---

## Notes

- Settings.gradle already had `gradlePluginPortal()` but app-level repositories also needed it
- Aliyun mirrors added as additional fallback for international CI runners
- No version change needed for osdetector plugin itself
