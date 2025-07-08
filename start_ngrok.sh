#!/bin/bash

# Ativa o ambiente virtual
source venv/bin/activate

# Carrega variáveis do .env (se quiser)
export $(grep -v '^#' .env | xargs)

# Executa o Django em segundo plano
echo "Iniciando servidor Django em http://127.0.0.1:8000"
python manage.py runserver &

# Aguarda 2 segundos
sleep 2

# Inicia o ngrok
echo "Iniciando túnel ngrok para porta 8000..."
ngrok http 8000
