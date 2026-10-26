@echo off
setlocal
title Pufi Kids - Animation Library Upload

set "ROOT=C:\Users\hakan\Desktop\children_video_library_automation"
set "BATCH_DIR=%ROOT%\output\upload_batch_generated"
set "SCRIPT=%TEMP%\pufi_upload_animation_library.py"
set "SCRIPT_URL=https://raw.githubusercontent.com/dewadam/cocuk-sarkilari-youtube/main/scripts/upload_animation_library.py"
set "TAG_FILE=%BATCH_DIR%\.pufi-release-tag"

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
  echo GitHub CLI is missing. Trying automatic installation with winget...
  where winget >nul 2>&1
  if errorlevel 1 (
    echo ERROR: winget is not available on this Windows installation.
    echo Install GitHub CLI from https://cli.github.com/ and run this file again.
    goto :finish_error
  )
  winget install --id GitHub.cli --exact --silent --accept-package-agreements --accept-source-agreements
  if errorlevel 1 (
    echo ERROR: Automatic GitHub CLI installation failed.
    echo Install it from https://cli.github.com/ and run this file again.
    goto :finish_error
  )
  set "PATH=%PATH%;%ProgramFiles%\GitHub CLI;%LOCALAPPDATA%\Programs\GitHub CLI"
)

where gh >nul 2>&1
if errorlevel 1 (
  if exist "%ProgramFiles%\GitHub CLI\gh.exe" (
    set "GH_EXE=%ProgramFiles%\GitHub CLI\gh.exe"
  ) else if exist "%LOCALAPPDATA%\Programs\GitHub CLI\gh.exe" (
    set "GH_EXE=%LOCALAPPDATA%\Programs\GitHub CLI\gh.exe"
  ) else (
    echo ERROR: GitHub CLI was installed but gh.exe could not be found.
    echo Restart Command Prompt and run this file again.
    goto :finish_error
  )
) else (
  set "GH_EXE=gh"
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

if exist "%TAG_FILE%" (
  set /p RELEASE_TAG=<"%TAG_FILE%"
) else (
  powershell -NoProfile -ExecutionPolicy Bypass -Command "$tag='animation-library-'+(Get-Date -Format 'yyyyMMdd-HHmmss'); Set-Content -NoNewline -Encoding ASCII -Path '%TAG_FILE%' -Value $tag"
  set /p RELEASE_TAG=<"%TAG_FILE%"
)
if not exist "%TAG_FILE%" (
  echo ERROR: Could not create a resumable upload tag file.
  goto :finish_error
)

echo Downloading the current uploader from the Pufi Kids GitHub repository...
powershell -NoProfile -ExecutionPolicy Bypass -Command "Invoke-WebRequest -UseBasicParsing -Uri '%SCRIPT_URL%' -OutFile '%SCRIPT%'"
if errorlevel 1 (
  echo ERROR: Could not download uploader script.
  goto :finish_error
)

"%GH_EXE%" auth status >nul 2>&1
if errorlevel 1 (
  echo GitHub login is required. Follow the browser/terminal prompts.
  "%GH_EXE%" auth login
  if errorlevel 1 goto :finish_error
)

echo.
echo Upload starts now. This uploads clips to GitHub Releases and updates catalog.json.
echo It does NOT upload anything to YouTube.
echo.
%PY_CMD% "%SCRIPT%" --batch-dir "%BATCH_DIR%" --repo "dewadam/cocuk-sarkilari-youtube" --tag "%RELEASE_TAG%"
if errorlevel 1 goto :finish_error
if exist "%TAG_FILE%" del "%TAG_FILE%" >nul 2>&1

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
