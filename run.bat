@echo off
REM ===============================================================
REM      ██╗ █████╗ ███╗   ██╗ ██████╗
REM      ██║██╔══██╗████╗  ██║██╔═══██╗
REM      ██║███████║██╔██╗ ██║██║   ██║
REM ██   ██║██╔══██║██║╚██╗██║██║   ██║
REM ╚█████╔╝██║  ██║██║ ╚████║╚██████╔╝
REM  ╚════╝ ╚═╝  ╚═╝╚═╝  ╚═══╝ ╚═════╝
REM
REM      Unified Security Configuration ^& Testing System
REM ===============================================================

setlocal enabledelayedexpansion

echo ===============================================================
echo      ██╗ █████╗ ███╗   ██╗ ██████╗
echo      ██║██╔══██╗████╗  ██║██╔═══██╗
echo      ██║███████║██╔██╗ ██║██║   ██║
echo ██   ██║██╔══██║██║╚██╗██║██║   ██║
echo ╚█████╔╝██║  ██║██║ ╚████║╚██████╔╝
echo  ╚════╝ ╚═╝  ╚═╝╚═╝  ╚═══╝ ╚═════╝
echo.
echo      Unified Security Configuration ^& Testing System
echo ===============================================================
echo.
echo This script will set up virtual environments and launch all Jano components.
echo.

echo [*] Checking required dependencies...

REM Check Python
python --version > nul 2>&1
if %errorlevel% neq 0 (
    echo [-] Python is not installed. Please install it before continuing.
    pause
    exit /b 1
)

REM Check pip
pip --version > nul 2>&1
if %errorlevel% neq 0 (
    echo [-] pip is not installed. Please install it before continuing.
    pause
    exit /b 1
)

REM Check venv
python -c "import venv" > nul 2>&1
if %errorlevel% neq 0 (
    echo [*] The venv module is not available. Trying to install it...
    pip install virtualenv
    if %errorlevel% neq 0 (
        echo [-] Could not install virtualenv. Please install it manually.
        pause
        exit /b 1
    )
)

echo [+] All dependencies are satisfied.

REM Setup Argos environment
echo [*] Setting up the Argos environment...

REM Create virtual environment for Argos
if not exist ".\argos_venv\" (
    python -m venv .\argos_venv
    if %errorlevel% neq 0 (
        echo [-] Could not create virtual environment for Argos.
        pause
        exit /b 1
    )
    echo [+] Argos virtual environment created.
) else (
    echo [*] Argos virtual environment already exists. Using existing one.
)

REM Activate virtual environment and install dependencies
call .\argos_venv\Scripts\activate.bat
echo [*] Installing Argos dependencies...
pip install -r argos\requirements.txt
if %errorlevel% neq 0 (
    call .\argos_venv\Scripts\deactivate.bat
    echo [-] Error installing Argos dependencies.
    pause
    exit /b 1
)

REM Configure .env file if it doesn't exist
if not exist ".\argos\.env" (
    echo [*] Configuring Argos .env file...
    copy .\argos\.env.example .\argos\.env

    REM Generate random API password
    set "characters=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
    set "API_PASSWORD="

    REM Generate a 16-character random password
    for /L %%i in (1,1,16) do (
        set /a random_index=!random! %% 62
        for /F %%j in ("!random_index!") do (
            set "c=!characters:~%%j,1!"
            set "API_PASSWORD=!API_PASSWORD!!c!"
        )
    )

    REM Replace the password in the .env file using findstr
    type .\argos\.env | findstr /v "JANO_API_PASSWORD" > .\argos\.env.tmp
    echo JANO_API_PASSWORD=!API_PASSWORD!>> .\argos\.env.tmp
    move /y .\argos\.env.tmp .\argos\.env > nul

    echo [+] Argos .env file configured.
    echo [*] Generated API password: !API_PASSWORD! (save this to configure other components)
) else (
    echo [*] Argos .env file already exists. Using existing configuration.
    for /f "tokens=2 delims==" %%a in ('type .\argos\.env ^| findstr "JANO_API_PASSWORD"') do (
        set "API_PASSWORD=%%a"
    )
)

call .\argos_venv\Scripts\deactivate.bat

REM Setup Eris environment
echo [*] Setting up the Eris environment...

REM Create virtual environment for Eris
if not exist ".\eris_venv\" (
    python -m venv .\eris_venv
    if %errorlevel% neq 0 (
        echo [-] Could not create virtual environment for Eris.
        pause
        exit /b 1
    )
    echo [+] Eris virtual environment created.
) else (
    echo [*] Eris virtual environment already exists. Using existing one.
)

REM Activate virtual environment and install dependencies
call .\eris_venv\Scripts\activate.bat
echo [*] Installing Eris dependencies...
pip install -r eris\requirements.txt
if %errorlevel% neq 0 (
    call .\eris_venv\Scripts\deactivate.bat
    echo [-] Error installing Eris dependencies.
    pause
    exit /b 1
)

REM Configure .env file if it doesn't exist
if not exist ".\eris\.env" (
    echo [*] Configuring Eris .env file...
    copy .\eris\.env.example .\eris\.env

    REM Update the .env file with the API password
    type .\eris\.env | findstr /v "JANO_API_PASSWORD" > .\eris\.env.tmp
    echo JANO_API_PASSWORD=!API_PASSWORD!>> .\eris\.env.tmp
    move /y .\eris\.env.tmp .\eris\.env > nul

    echo [+] Eris .env file configured.
) else (
    echo [*] Eris .env file already exists. Using existing configuration.
)

call .\eris_venv\Scripts\deactivate.bat

REM Setup Frontend environment
echo [*] Setting up the frontend environment...

REM Create virtual environment for the frontend
if not exist ".\frontend_venv\" (
    python -m venv .\frontend_venv
    if %errorlevel% neq 0 (
        echo [-] Could not create virtual environment for the frontend.
        pause
        exit /b 1
    )
    echo [+] Frontend virtual environment created.
) else (
    echo [*] Frontend virtual environment already exists. Using existing one.
)

REM Activate virtual environment and install dependencies
call .\frontend_venv\Scripts\activate.bat
echo [*] Installing frontend dependencies...
pip install -r frontend\requirements.txt
if %errorlevel% neq 0 (
    call .\frontend_venv\Scripts\deactivate.bat
    echo [-] Error installing frontend dependencies.
    pause
    exit /b 1
)

REM Configure .env file if it doesn't exist
if not exist ".\frontend\.env" (
    echo [*] Configuring frontend .env file...
    copy .\frontend\.env.example .\frontend\.env

    REM Update the .env file with the API password
    type .\frontend\.env | findstr /v "JANO_API_PASSWORD" > .\frontend\.env.tmp
    echo JANO_API_PASSWORD=!API_PASSWORD!>> .\frontend\.env.tmp
    move /y .\frontend\.env.tmp .\frontend\.env > nul

    echo [+] Frontend .env file configured.
) else (
    echo [*] Frontend .env file already exists. Using existing configuration.
)

call .\frontend_venv\Scripts\deactivate.bat

REM Start all components
echo [*] Starting Argos...
start /b cmd /c "call .\argos_venv\Scripts\activate.bat && cd argos && python -m argos -p 8005 && pause"
echo [+] Argos started (accessible only from localhost at http://localhost:8005)

timeout /t 2 > nul

echo [*] Starting Eris...
start /b cmd /c "call .\eris_venv\Scripts\activate.bat && cd eris && python -m eris -p 8006 && pause"
echo [+] Eris started (accessible only from localhost at http://localhost:8006)

timeout /t 2 > nul

echo [*] Starting the frontend...
start /b cmd /c "call .\frontend_venv\Scripts\activate.bat && cd frontend && streamlit run app.py --server.address=127.0.0.1 --server.port=8501 && pause"
echo [+] Frontend started (accessible only from localhost at http://localhost:8501)

echo.
echo [+] Jano is now running!
echo [*] Argos: http://localhost:8005
echo [*] Eris: http://localhost:8006
echo [*] Frontend: http://localhost:8501
echo [*] Close all command windows to stop all services.

REM Keep the script running until user decides to exit
echo.
echo Press any key to exit this window (services will continue running in background windows)...
pause > nul

endlocal