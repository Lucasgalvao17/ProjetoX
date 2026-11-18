@echo off
setlocal
title ATILA V2 - Gestao de Salas
cd /d "%~dp0"

if not exist "app.py" (
 echo ERRO: app.py nao encontrado.
 pause
 exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
 echo Criando ambiente virtual...
 py -m venv .venv
 if errorlevel 1 python -m venv .venv
)

echo Instalando dependencias...
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (
 echo Erro na instalacao.
 pause
 exit /b 1
)

echo Iniciando ATILA...
".venv\Scripts\python.exe" -m streamlit run app.py
pause
endlocal
