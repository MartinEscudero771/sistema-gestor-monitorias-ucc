@echo off
setlocal
chcp 65001 >nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
cd /d "%~dp0"

rem Argumentos opcionales:
rem   iniciar.bat --reset        reconstruye la base con datos de demo
rem   iniciar.bat --sin-tests    arranca sin ejecutar la suite de pruebas
set "BANDERA_RESET="
set "SALTAR_TESTS="
if /I "%~1"=="--reset" set "BANDERA_RESET=--reset"
if /I "%~1"=="--sin-tests" set "SALTAR_TESTS=1"
if /I "%~2"=="--sin-tests" set "SALTAR_TESTS=1"
if /I "%~1"=="--reset" if /I "%~2"=="--reset" set "BANDERA_RESET=--reset"

echo Intentando iniciar MariaDB/MySQL si esta detenido...
sc query MariaDB 2>nul | findstr /I "RUNNING" >nul
if errorlevel 1 (
    net start MariaDB >nul 2>nul
)
sc query MySQL 2>nul | findstr /I "RUNNING" >nul
if errorlevel 1 (
    net start MySQL >nul 2>nul
)

if exist ".venv\Scripts\python.exe" goto entorno_listo
echo Creando entorno virtual...
where py >nul 2>nul
if errorlevel 1 goto usar_python
py -3 -m venv .venv
if errorlevel 1 goto error
goto instalar
:usar_python
python -m venv .venv
if errorlevel 1 goto error
:instalar
echo Instalando dependencias...
if exist "backend\requirements.txt" (
    ".venv\Scripts\python.exe" -m pip install --disable-pip-version-check -r "backend\requirements.txt"
) else (
    ".venv\Scripts\python.exe" -m pip install --disable-pip-version-check -r "requirements.txt"
)
if errorlevel 1 goto error
goto verificar
:entorno_listo
".venv\Scripts\python.exe" -c "import fastapi, uvicorn, pymysql, argon2, jwt, dotenv" >nul 2>nul
if errorlevel 1 goto instalar
:verificar
echo Verificando la base de datos...
pushd "backend"
"..\.venv\Scripts\python.exe" "preparar_bd.py" %BANDERA_RESET%
set "CODIGO=%ERRORLEVEL%"
popd
if not "%CODIGO%"=="0" (
    echo.
    echo No se pudo dejar lista la base de datos. Revise backend\.env.
    pause
    exit /b 1
)
echo Credenciales fijas de demostracion: credenciales.txt (raiz del proyecto).

if not defined SALTAR_TESTS goto correr_tests
echo.
echo Pruebas automatizadas omitidas (--sin-tests).
goto preparar_arranque

:correr_tests
echo.
echo Ejecutando pruebas automatizadas (backend/tests)...
pushd "backend"
"..\.venv\Scripts\python.exe" -m pytest tests -q --tb=short
set "CODIGO_TESTS=%ERRORLEVEL%"
popd
if not "%CODIGO_TESTS%"=="0" (
    echo.
    echo Las pruebas automatizadas fallaron. Revise la salida anterior.
    echo Para saltarlas de este arranque use: iniciar.bat --sin-tests
    pause
    exit /b 1
)

:preparar_arranque
echo.
for /f "tokens=2 delims==" %%P in ('findstr /R "^PUERTO_SERVIDOR=" "backend\.env" 2^>nul') do set PUERTO=%%P
if not defined PUERTO set PUERTO=8080
echo Iniciando el sistema en http://127.0.0.1:%PUERTO%
echo Presione Ctrl+C para detener el servidor.
echo.
start "" powershell -NoProfile -WindowStyle Hidden -Command "Start-Sleep -Seconds 3; Start-Process 'http://127.0.0.1:%PUERTO%'"
pushd "backend"
"..\.venv\Scripts\python.exe" "iniciar.py"
set "CODIGO=%ERRORLEVEL%"
popd
if not "%CODIGO%"=="0" goto error
exit /b 0
:error
echo.
echo No se pudo iniciar el sistema. Revise los mensajes anteriores.
pause
exit /b 1
