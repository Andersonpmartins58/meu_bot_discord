#!/bin/bash

# Este script garante que as dependências sejam instaladas antes de iniciar o bot.

# 1. Instala as dependências básicas do arquivo requirements.txt
echo "--- Instalando dependências básicas ---"
python -m pip install -r requirements.txt

# 2. Força a atualização do yt-dlp para a versão mais recente
echo "--- Forçando a atualização do yt-dlp ---"
python -m pip install --upgrade yt-dlp

# 3. Inicia o bot do Discord
echo "--- Dependências prontas. Iniciando o bot... ---"
python bot_discord.py

