#!/bin/bash

# Este script garante que as dependências sejam instaladas antes de iniciar o bot.

# 1. Instala/atualiza as dependências do arquivo requirements.txt
echo "--- Forçando a instalação das dependências ---"
python -m pip install -r requirements.txt

# 2. Inicia o bot do Discord
echo "--- Dependências instaladas. Iniciando o bot... ---"
python discord_music_bot.py
