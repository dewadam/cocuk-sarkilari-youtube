@echo off
setlocal
title Pufi Kids - Animation Library Upload

set "ROOT=C:\Users\hakan\Desktop\children_video_library_automation"
set "BATCH_DIR=%ROOT%\output\upload_batch_generated"
set "SCRIPT=%TEMP%\pufi_upload_animation_library.py"
set "SCRIPT_URL=https://raw.githubusercontent.com/dewadam/cocuk-sarkilari-youtube/main/scripts/upload_animation_library.py"

echo ============================================
echo Pufi Kids - 500 Clip Animation Library Upload
echo ============================================
echo.

if not exist "%BATCH_DIR%" (
  echo ERROR: Batch folder not found:
  echo %BATCH_DIR%
  echo First run the JSON preparation script.
  goto :finish_error
)

where gh >nul 2>&1
if errorlevel 1 (
  echo ERROR: GitHub CLI is not installed.
  echo Install GitHub CLI: https://cli.github.com/
  goto :finish_error
)

where git >nul 2>&1
if errorlevel 1 (
  echo ERROR: Git for Windows is not installed.
  echo Install Git: https://git-scm.com/download/win
  goto :finish_error
)

where py >nul 2>&1
if errorlevel 1 (
  where python >nul 2>&1
  if errorlevel 1 (
    echo ERROR: Python is not installed or not on PATH.
    goto :finish_error
  )
  set "PY_CMD=python"
) else (
  set "PY_CMD=py"
)

echo Downloading the current uploader from the Pufi Kids GitHub repository...
powershell -NoProfile -ExecutionPolicy Bypass -Command "Invoke-WebRequest -UseBasicParsing -Uri '%SCRIPT_URL%' -OutFile '%SCRIPT%'"
if errorlevel 1 (
  echo ERROR: Could not download uploader script.
  goto :finish_error
)

gh auth status >nul 2>&1
if errorlevel 1 (
  echo GitHub login is required. Follow the browser/terminal prompts.
  gh auth login
  if errorlevel 1 goto :finish_error
)

echo.
echo Upload starts now. This uploads clips to GitHub Releases and updates catalog.json.
echo It does NOT upload anything to YouTube.
echo.
%PY_CMD% "%SCRIPT%" --batch-dir "%BATCH_DIR%" --repo "dewadam/cocuk-sarkilari-youtube"
if errorlevel 1 goto :finish_error

echo.
echo SUCCESS: Animation library upload and catalog update completed.
goto :finish

:finish_error
echo.
echo The upload did not complete. Read the error above before retrying.

:finish
echo.
pause
endlocal
