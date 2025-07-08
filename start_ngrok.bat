@echo off

REM Ativa o ambiente virtual
call venv\Scripts\activate.bat

REM Executa o Django em segundo plano
start /B python manage.py runserver

REM Espera um pouco para iniciar o servidor
timeout /t 2 > NUL

REM Inicia o ngrok
ngrok http 8000
