@echo off
echo ========================================
echo CHECKING FLUTTER CODE BEFORE COMMIT
echo ========================================
echo.

cd flutter

echo [1/3] Running Flutter Analyze...
flutter analyze
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Flutter analyze failed!
    echo Please fix the errors before committing.
    exit /b 1
)

echo.
echo [2/3] Running Dart Format Check...
dart format --set-exit-if-changed lib/
if %errorlevel% neq 0 (
    echo.
    echo [WARNING] Code formatting issues found.
    echo Run: dart format lib/
)

echo.
echo [3/3] Checking for syntax errors in key files...
flutter pub run build_runner build --delete-conflicting-outputs --dry-run 2>&1 | findstr /C:"SEVERE" /C:"error"
if %errorlevel% equ 0 (
    echo.
    echo [ERROR] Build runner found errors!
    echo Please fix before committing.
    exit /b 1
)

echo.
echo ========================================
echo [SUCCESS] All checks passed!
echo ========================================
echo You can now commit and push safely.
exit /b 0

