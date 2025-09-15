# -*- coding: utf-8 -*-

# ---------------------------------------------------------------------------
#                BOT DE MÚSICA SIMPLES PARA DISCORD
# ---------------------------------------------------------------------------
#
# Instruções de configuração:
#
# 1. Instale as bibliotecas necessárias:
#    pip install discord.py yt-dlp PyNaCl Flask
#
# 2. Baixe e instale o FFmpeg:
#    - Vá para: https://ffmpeg.org/download.html
#    - Baixe a versão para o seu sistema operacional.
#    - Extraia os arquivos e adicione a pasta 'bin' ao PATH do seu sistema.
#      (Isso é crucial para o bot conseguir processar o áudio).
#
# 3. Crie um Bot no Portal de Desenvolvedores do Discord:
#    - Vá para: https://discord.com/developers/applications
#    - Clique em "New Application".
#    - Dê um nome ao seu bot.
#    - Vá para a aba "Bot".
#    - Clique em "Add Bot".
#    - Ative as "Privileged Gateway Intents":
#        - SERVER MEMBERS INTENT
#        - MESSAGE CONTENT INTENT
#    - Na seção "Token", clique em "Reset Token" ou "Copy" para obter seu token.
#      NÃO COMPARTILHE ESSE TOKEN COM NINGUÉM!
#
# 4. Adicione o bot ao seu servidor:
#    - Vá para a aba "OAuth2" -> "URL Generator".
#    - Marque as scopes "bot" e "applications.commands".
#    - Em "Bot Permissions", marque:
#        - Connect
#        - Speak
#        - Send Messages
#        - Read Message History
#    - Copie a URL gerada e cole no seu navegador para convidar o bot.
#
# 5. Execute o bot:
#    - Cole seu token na variável `TOKEN` abaixo.
#    - Salve o arquivo como, por exemplo, `discord_music_bot.py`.
#    - No terminal, execute: python discord_music_bot.py
#
# Comandos no Discord:
#    #dentro  - Faz o bot entrar no canal de voz em que você está.
#    #play [URL_do_YouTube] - Toca a música ou playlist do link do YouTube.
#    #fila - Mostra as próximas músicas da fila.
#    #pular  - Pula para a próxima música da fila.
#    #leave - Faz o bot sair do canal de voz.
#    #ajuda - Mostra esta lista de comandos.
#
# ---------------------------------------------------------------------------

import discord
import yt_dlp
import asyncio
import os # Importado para ler o token do ambiente
from flask import Flask # Importado para o servidor web
from threading import Thread # Importado para rodar o servidor e o bot juntos

# --- Bloco para manter o bot online (Servidor Web) ---
app = Flask('')

@app.route('/')
def home():
    return "O bot de música está no ar!"

def run():
  app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()
# --- Fim do Bloco ---


# --- Configuração ---
# O token será lido das "Secrets" do Replit, não mais diretamente do código.
TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    print("[ERRO] Token não encontrado! Certifique-se de configurar a Secret 'DISCORD_TOKEN' no Replit.")

# --- Fim da Configuração ---

# Configura as intenções (intents) do bot.
# Precisamos de permissões para ler mensagens e acessar canais de voz.
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.voice_states = True

# Inicializa o cliente do bot
client = discord.Client(intents=intents)

# Fila de músicas para tocar
song_queue = []
is_playing = False

# Configurações para o yt-dlp (para baixar o áudio do YouTube)
YDL_OPTS = {
    'format': 'bestaudio/best',
    'quiet': True,
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }],
    # Novas opções para evitar bloqueios do YouTube:
    'ignoreerrors': True,  # Continua a playlist mesmo se um vídeo falhar
    'default_search': 'auto',
    'source_address': '0.0.0.0' # Pode ajudar com problemas de rede/IP
}

# Configurações do FFmpeg
# O `executable` aponta para o caminho do FFmpeg se não estiver no PATH.
# Se estiver no PATH, pode deixar como está.
FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

# Função para tocar a próxima música da fila
async def play_next(message):
    global is_playing
    if len(song_queue) > 0:
        is_playing = True
        song_info = song_queue.pop(0) # Pega o dicionário {'url': ..., 'title': ...}
        url = song_info['url']
        title = song_info['title']
        voice_client = discord.utils.get(client.voice_clients, guild=message.guild)

        if voice_client and voice_client.is_connected():
            try:
                # Precisamos usar o ydl para pegar a URL do áudio, mesmo que já tenhamos o título
                with yt_dlp.YoutubeDL(YDL_OPTS) as ydl:
                    info = ydl.extract_info(url, download=False)
                    audio_url = info['url']
                
                source = discord.FFmpegPCMAudio(audio_url, **FFMPEG_OPTIONS)
                
                # Toca o áudio e, quando terminar, chama play_next novamente
                voice_client.play(source, after=lambda e: asyncio.run_coroutine_threadsafe(play_next(message), client.loop))
                
                # Usamos o título que já guardamos ao adicionar na fila
                await message.channel.send(f'🎶 Tocando agora: **{title}**')

            except Exception as e:
                await message.channel.send(f'Ocorreu um erro ao tentar tocar a música: {e}')
                is_playing = False
        else:
            is_playing = False
    else:
        is_playing = False
        await message.channel.send('Fila de músicas vazia.')

# Evento que é acionado quando o bot está pronto e conectado
@client.event
async def on_ready():
    print(f'Bot conectado como {client.user}')
    print('-----------------------------------------')
    print('Bot está pronto para receber comandos!')
    print('-----------------------------------------')

# Evento que é acionado a cada mensagem enviada no servidor
@client.event
async def on_message(message):
    global is_playing
    # Ignora mensagens enviadas pelo próprio bot
    if message.author == client.user:
        return

    # Converte a mensagem para minúsculas para facilitar a leitura dos comandos
    content = message.content.lower()
    
    # --- Comando #dentro ---
    # Faz o bot entrar no canal de voz do autor da mensagem
    if content.startswith('#dentro'):
        if message.author.voice:
            channel = message.author.voice.channel
            try:
                await channel.connect()
                await message.channel.send(f'✅ Oi,amor!:): **{channel.name}**')
            except discord.ClientException:
                await message.channel.send('Já estou em um canal de voz.')
            except Exception as e:
                await message.channel.send(f'Ocorreu um erro ao conectar: {e}')
        else:
            await message.channel.send('Você precisa estar em um canal de voz para me convidar!')

    # --- Comando #play [URL] ---
    # Adiciona uma música ou playlist à fila e começa a tocar se não estiver tocando
    elif content.startswith('#play'):
        if not message.author.voice:
            await message.channel.send("Você precisa estar em um canal de voz para tocar música!")
            return

        voice_client = discord.utils.get(client.voice_clients, guild=message.guild)
        if not voice_client or not voice_client.is_connected():
            await message.channel.send("Não estou conectado a um canal de voz. Use `#dentro` primeiro.")
            return

        try:
            # Pega a URL da mensagem, permitindo URLs com espaços
            url = message.content.split(' ', 1)[1]
            
            # Usar o yt-dlp para extrair informações e verificar se é uma playlist
            with yt_dlp.YoutubeDL(YDL_OPTS) as ydl:
                info = ydl.extract_info(url, download=False)

            # Se for uma playlist (contém 'entries')
            if 'entries' in info:
                playlist_entries = info['entries']
                for entry in playlist_entries:
                    # Garantir que temos uma URL e título válidos para cada item
                    if entry and 'webpage_url' in entry and 'title' in entry:
                        song_queue.append({'url': entry['webpage_url'], 'title': entry['title']})
                
                await message.channel.send(f'🎵 Playlist adicionada! **{len(playlist_entries)}** músicas foram adicionadas à fila.')
            
            # Se for um único vídeo
            else:
                song_queue.append({'url': url, 'title': info['title']})
                await message.channel.send(f'🎵 Adicionado à fila: **{info["title"]}**')
            
            # Se não estiver tocando nada, inicia a reprodução
            if not is_playing:
                await play_next(message)

        except IndexError:
            await message.channel.send('Por favor, forneça uma URL do YouTube após o comando `#play`.')
        except Exception as e:
            await message.channel.send(f"Ocorreu um erro ao processar o link: {e}")

    # --- Comando #ajuda ---
    # Mostra a lista de todos os comandos disponíveis
    elif content.startswith('#ajuda'):
        help_message = """
```
📜 LISTA DE COMANDOS DO BOT 📜

#dentro
    » Faz o bot entrar no seu canal de voz.

#play [https://www.youtube.com/](https://www.youtube.com/)
    » Toca uma música ou playlist do YouTube.

#fila
    » Mostra as próximas 10 músicas na fila.

#pular
    » Pula para a próxima música da fila.

#tchau
    » Faz o bot sair do canal de voz e limpar a fila.

#ajuda
    » Mostra esta mensagem de ajuda.
```
"""
        await message.channel.send(help_message)

    # --- Comando #fila ---
    # Mostra a fila de músicas
    elif content.startswith('#fila'):
        if not song_queue:
            await message.channel.send('A fila de músicas está vazia.')
            return

        # Monta a mensagem com a lista de músicas
        queue_list = "```"
        # Mostra no máximo as próximas 10 músicas para não poluir o chat
        for i, song_info in enumerate(song_queue[:10]):
            queue_list += f"{i+1}. {song_info['title']}\n"
        
        if len(song_queue) > 10:
            queue_list += f"\n... e mais {len(song_queue) - 10} música(s)."
        
        queue_list += "```"
        
        await message.channel.send(f'**Próximas músicas na fila:**\n{queue_list}')

    # --- Comando #pular ---
    # Pula a música que está tocando
    elif content.startswith('#pular'):
        voice_client = discord.utils.get(client.voice_clients, guild=message.guild)
        if voice_client and voice_client.is_playing():
            voice_client.stop()
            await message.channel.send('⏭️ Música pulada!')
        else:
            await message.channel.send('Não estou tocando nenhuma música no momento para pular.')

    # --- Comando #leave ---
    # Desconecta o bot do canal de voz
    elif content.startswith('#tchau'):
        voice_client = discord.utils.get(client.voice_clients, guild=message.guild)
        if voice_client and voice_client.is_connected():
            song_queue.clear() # Limpa a fila ao sair
            is_playing = False
            await voice_client.disconnect()
            await message.channel.send('👋 Estou indo embora!.')
        else:
            await message.channel.send('Não estou em um canal de voz.')

# Inicia o servidor web para manter o bot online
keep_alive()
            
# Roda o bot com o token fornecido
try:
    if TOKEN:
        client.run(TOKEN)
except discord.errors.LoginFailure:
    print("\n[ERRO] O token fornecido é inválido. Verifique o token nas Secrets.")
except Exception as e:
    print(f"\n[ERRO] Ocorreu um erro inesperado: {e}")

