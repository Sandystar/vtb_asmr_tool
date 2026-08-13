@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"
if errorlevel 1 goto :failure

set "USE_SAMPLE=0"
if /i "%~1"=="sample" set "USE_SAMPLE=1"
if not "%~1"=="" if "!USE_SAMPLE!"=="0" (
    echo [ERROR] Unsupported argument: %~1
    echo [ERROR] Usage: batch_build.bat [sample]
    goto :failure
)
if not "%~2"=="" (
    echo [ERROR] Usage: batch_build.bat [sample]
    goto :failure
)

set "REQUIRED_PYTHON_MAJOR=3"
set "REQUIRED_PYTHON_MINOR=13"
set "VENV_DIR=.venv"
set "VENV_PYTHON=%VENV_DIR%\Scripts\python.exe"
set "BUILD_HASH_FILE=%VENV_DIR%\.installed-build-hash"
set "CURRENT_HASH_FILE=%VENV_DIR%\.current-build-hash"
set "BUILD_TEMP=%CD%\.build-temp"
set "PLAYWRIGHT_STAGE=%BUILD_TEMP%\ms-playwright"
set "PYINSTALLER_DIST=%BUILD_TEMP%\dist"
set "PYINSTALLER_WORK=%BUILD_TEMP%\work"
set "PYINSTALLER_SPEC=%BUILD_TEMP%\spec"
set "PACKAGE_STAGE=%BUILD_TEMP%\package"
set "PUBLISH_STAGE=%BUILD_TEMP%\publish"
set "PREVIOUS_OUTPUT=%BUILD_TEMP%\previous-build"
set "OUTPUT_DIR=build"
set "VERSION_TEXT_FILE=%BUILD_TEMP%\app_version.txt"
set "VERSION_FILE=%BUILD_TEMP%\version_info.txt"

if "!USE_SAMPLE!"=="1" (
    set "CONFIG_SOURCE=config.sample"
) else (
    set "CONFIG_SOURCE=config"
)

call :find_python
if errorlevel 1 goto :failure
call :ensure_virtual_environment
if errorlevel 1 goto :failure
call :ensure_build_dependencies
if errorlevel 1 goto :failure
call :ensure_playwright_chromium
if errorlevel 1 goto :failure
call :validate_package_sources
if errorlevel 1 goto :failure
call :prepare_build_metadata
if errorlevel 1 goto :failure
call :build_executable
if errorlevel 1 goto :failure
call :assemble_package
if errorlevel 1 goto :failure
call :create_archive
if errorlevel 1 goto :failure
call :publish_package
if errorlevel 1 goto :failure

call :cleanup
if errorlevel 1 goto :failure

echo.
echo [INFO] Windows package created: %OUTPUT_DIR%\%ARCHIVE_FILENAME%
exit /b 0

:find_python
set "PYTHON_LAUNCHER="
py -%REQUIRED_PYTHON_MAJOR%.%REQUIRED_PYTHON_MINOR% -c "import sys; raise SystemExit(0 if sys.version_info[:2] == (%REQUIRED_PYTHON_MAJOR%, %REQUIRED_PYTHON_MINOR%) else 1)" >nul 2>&1
if not errorlevel 1 set "PYTHON_LAUNCHER=py -%REQUIRED_PYTHON_MAJOR%.%REQUIRED_PYTHON_MINOR%"

if not defined PYTHON_LAUNCHER (
    python -c "import sys; raise SystemExit(0 if sys.version_info[:2] == (%REQUIRED_PYTHON_MAJOR%, %REQUIRED_PYTHON_MINOR%) else 1)" >nul 2>&1
    if not errorlevel 1 set "PYTHON_LAUNCHER=python"
)

if defined PYTHON_LAUNCHER exit /b 0
echo [ERROR] Python %REQUIRED_PYTHON_MAJOR%.%REQUIRED_PYTHON_MINOR% is required.
exit /b 1

:ensure_virtual_environment
if exist "%VENV_PYTHON%" (
    "%VENV_PYTHON%" -c "import sys; raise SystemExit(0 if sys.version_info[:2] == (%REQUIRED_PYTHON_MAJOR%, %REQUIRED_PYTHON_MINOR%) else 1)" >nul 2>&1
    if errorlevel 1 (
        echo [INFO] Rebuilding incompatible virtual environment...
        rmdir /s /q "%VENV_DIR%"
        if exist "%VENV_PYTHON%" exit /b 1
    )
)

if not exist "%VENV_PYTHON%" (
    echo [INFO] Creating Python %REQUIRED_PYTHON_MAJOR%.%REQUIRED_PYTHON_MINOR% virtual environment...
    %PYTHON_LAUNCHER% -m venv "%VENV_DIR%"
    if errorlevel 1 exit /b 1
)

"%VENV_PYTHON%" -m pip --version >nul 2>&1
if not errorlevel 1 exit /b 0

echo [INFO] Restoring pip...
"%VENV_PYTHON%" -m ensurepip --upgrade
if errorlevel 1 exit /b 1
exit /b 0

:ensure_build_dependencies
if not exist "pyproject.toml" (
    echo [ERROR] Missing dependency definition: pyproject.toml
    exit /b 1
)

"%VENV_PYTHON%" -c "from pathlib import Path; import hashlib; source=Path('pyproject.toml').read_bytes(); Path(r'%CURRENT_HASH_FILE%').write_text(hashlib.sha256(source).hexdigest(), encoding='ascii')"
if errorlevel 1 exit /b 1
set "PROJECT_HASH="
set /p PROJECT_HASH=<"%CURRENT_HASH_FILE%"
del /q "%CURRENT_HASH_FILE%" >nul 2>&1
if not defined PROJECT_HASH exit /b 1

set "INSTALLED_HASH="
if exist "%BUILD_HASH_FILE%" set /p INSTALLED_HASH=<"%BUILD_HASH_FILE%"
if not "!PROJECT_HASH!"=="!INSTALLED_HASH!" goto :install_build_dependencies

call :build_dependencies_healthy
if not errorlevel 1 exit /b 0

:install_build_dependencies
echo [INFO] Installing or repairing build dependencies...
"%VENV_PYTHON%" -m pip install --disable-pip-version-check -e ".[build]"
if errorlevel 1 exit /b 1
call :build_dependencies_healthy
if errorlevel 1 exit /b 1
"%VENV_PYTHON%" -c "from pathlib import Path; Path(r'%BUILD_HASH_FILE%').write_text(r'!PROJECT_HASH!', encoding='ascii')"
if errorlevel 1 exit /b 1
exit /b 0

:build_dependencies_healthy
"%VENV_PYTHON%" -c "import PyInstaller, playwright.sync_api, PySide6.QtWidgets, spider_vtbasmr_gui; parts=tuple(int(part) for part in PyInstaller.__version__.split('.')[:2]); raise SystemExit(0 if (6, 22) <= parts < (7, 0) else 1)" >nul 2>&1
if errorlevel 1 exit /b 1
"%VENV_PYTHON%" -m pip check >nul 2>&1
if errorlevel 1 exit /b 1
exit /b 0

:ensure_playwright_chromium
echo [INFO] Checking Playwright Chromium...
call :playwright_chromium_ready
if not errorlevel 1 exit /b 0

echo [INFO] Installing Playwright Chromium...
set "PLAYWRIGHT_DOWNLOAD_CONNECTION_TIMEOUT=120000"
"%VENV_PYTHON%" -m playwright install chromium
if errorlevel 1 exit /b 1
call :playwright_chromium_ready
if errorlevel 1 exit /b 1
exit /b 0

:playwright_chromium_ready
"%VENV_PYTHON%" -c "from pathlib import Path; from playwright.sync_api import sync_playwright; driver=sync_playwright().start(); chromium=Path(driver.chromium.executable_path); revision=chromium.parents[1].name.removeprefix('chromium-'); headless=chromium.parents[2] / ('chromium_headless_shell-' + revision) / 'chrome-headless-shell-win64' / 'chrome-headless-shell.exe'; driver.stop(); raise SystemExit(0 if chromium.is_file() and headless.is_file() else 1)" >nul 2>&1
exit /b %errorlevel%

:validate_package_sources
if not exist "%CONFIG_SOURCE%\" (
    echo [ERROR] Missing configuration directory: %CONFIG_SOURCE%
    exit /b 1
)
if not exist "thirdtool\" (
    echo [ERROR] Missing third-party tool directory: thirdtool
    exit /b 1
)
for %%F in (vtbasmr_base.json vtb_list.json fnos_baidu_netdisk.json 7zip.json) do (
    if not exist "%CONFIG_SOURCE%\%%F" (
        echo [ERROR] Missing configuration file: %CONFIG_SOURCE%\%%F
        exit /b 1
    )
)
exit /b 0

:prepare_build_metadata
if exist "%BUILD_TEMP%" rmdir /s /q "%BUILD_TEMP%"
mkdir "%BUILD_TEMP%"
if errorlevel 1 exit /b 1

"%VENV_PYTHON%" "tools\windows_build.py" version "pyproject.toml" --output "%VERSION_TEXT_FILE%"
if errorlevel 1 exit /b 1
set "APP_VERSION="
set /p APP_VERSION=<"%VERSION_TEXT_FILE%"
if not defined APP_VERSION (
    echo [ERROR] Unable to read the semantic version from pyproject.toml.
    exit /b 1
)
set "APP_BASENAME=vtb_asmr_tool_gui_v!APP_VERSION!"
set "APP_FILENAME=!APP_BASENAME!.exe"
set "ARCHIVE_FILENAME=!APP_BASENAME!.zip"

"%VENV_PYTHON%" "tools\windows_build.py" write-version-file "pyproject.toml" "%VERSION_FILE%"
if errorlevel 1 exit /b 1
"%VENV_PYTHON%" "tools\windows_build.py" stage-playwright "%PLAYWRIGHT_STAGE%"
if errorlevel 1 exit /b 1
exit /b 0

:build_executable
echo [INFO] Building %APP_FILENAME%...
"%VENV_PYTHON%" -m PyInstaller ^
    --noconfirm ^
    --clean ^
    --onefile ^
    --windowed ^
    --noupx ^
    --name "%APP_BASENAME%" ^
    --distpath "%PYINSTALLER_DIST%" ^
    --workpath "%PYINSTALLER_WORK%" ^
    --specpath "%PYINSTALLER_SPEC%" ^
    --paths "src" ^
    --collect-all "playwright" ^
    --hidden-import "playwright.sync_api" ^
    --add-data "%PLAYWRIGHT_STAGE%;ms-playwright" ^
    --version-file "%VERSION_FILE%" ^
    "src\spider_vtbasmr_gui\__main__.py"
if errorlevel 1 exit /b 1

if not exist "%PYINSTALLER_DIST%\%APP_FILENAME%" (
    echo [ERROR] PyInstaller did not create the expected executable.
    exit /b 1
)

echo [INFO] Verifying bundled runtime and Chromium...
"%PYINSTALLER_DIST%\%APP_FILENAME%" --check-runtime
if errorlevel 1 (
    echo [ERROR] The bundled executable failed its runtime self-check.
    exit /b 1
)
exit /b 0

:assemble_package
mkdir "%PACKAGE_STAGE%"
if errorlevel 1 exit /b 1
copy /y "%PYINSTALLER_DIST%\%APP_FILENAME%" "%PACKAGE_STAGE%\%APP_FILENAME%" >nul
if errorlevel 1 exit /b 1
xcopy /e /i /h /y "%CONFIG_SOURCE%" "%PACKAGE_STAGE%\config" >nul
if errorlevel 1 exit /b 1
xcopy /e /i /h /y "thirdtool" "%PACKAGE_STAGE%\thirdtool" >nul
if errorlevel 1 exit /b 1

if not exist "%PACKAGE_STAGE%\%APP_FILENAME%" exit /b 1
if not exist "%PACKAGE_STAGE%\config\vtbasmr_base.json" exit /b 1
if not exist "%PACKAGE_STAGE%\thirdtool\" exit /b 1
exit /b 0

:create_archive
mkdir "%PUBLISH_STAGE%"
if errorlevel 1 exit /b 1
echo [INFO] Compressing %ARCHIVE_FILENAME%...
"%VENV_PYTHON%" "tools\windows_build.py" create-archive "%PACKAGE_STAGE%" "%PUBLISH_STAGE%\%ARCHIVE_FILENAME%"
if errorlevel 1 exit /b 1
if not exist "%PUBLISH_STAGE%\%ARCHIVE_FILENAME%" (
    echo [ERROR] The expected ZIP archive was not created.
    exit /b 1
)
exit /b 0

:publish_package
if exist "%PREVIOUS_OUTPUT%" rmdir /s /q "%PREVIOUS_OUTPUT%"
if exist "%OUTPUT_DIR%" (
    move "%OUTPUT_DIR%" "%PREVIOUS_OUTPUT%" >nul
    if errorlevel 1 exit /b 1
)
move "%PUBLISH_STAGE%" "%OUTPUT_DIR%" >nul
if errorlevel 1 (
    if exist "%PREVIOUS_OUTPUT%" move "%PREVIOUS_OUTPUT%" "%OUTPUT_DIR%" >nul
    exit /b 1
)
if exist "%PREVIOUS_OUTPUT%" rmdir /s /q "%PREVIOUS_OUTPUT%"
if exist "%PREVIOUS_OUTPUT%" exit /b 1
exit /b 0

:cleanup
if exist "%BUILD_TEMP%" rmdir /s /q "%BUILD_TEMP%"
if exist "%BUILD_TEMP%" exit /b 1
exit /b 0

:failure
call :cleanup >nul 2>&1
echo.
echo [ERROR] Windows build failed. Review the error output above.
exit /b 1