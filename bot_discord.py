# -*- coding: utf-8 -*-

# ---------------------------------------------------------------------------
#                BOT DE MÚSICA SIMPLES PARA DISCORD
# ---------------------------------------------------------------------------
#
# Versão preparada para hospedagem 24/7 em serviços como Render ou Replit.
#
# ---------------------------------------------------------------------------

import discord
import yt_dlp
import asyncio
import os
from flask import Flask
from threading import Thread

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
# O token será lido das "Environment Variables" (Render) ou "Secrets" (Replit).
TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    print("[ERRO] Token não encontrado! Certifique-se de configurar a variável de ambiente 'DISCORD_TOKEN'.")

# --- Fim da Configuração ---

# Configura as intenções (intents) do bot.
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.voice_states = True

# Inicializa o cliente do bot
client = discord.Client(intents=intents)

# Variáveis globais para gerenciar a fila e o estado de reprodução
song_queue = []
is_playing = False

# Configurações para o yt-dlp
YDL_OPTS = {
    'format': 'bestaudio/best',
    'quiet': True,
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }],
    'noplaylist': False
}

# Configurações do FFmpeg
FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

# Função para tocar a próxima música da fila
async def play_next(message):
    global is_playing
    if len(song_queue) > 0:
        is_playing = True
        song_info = song_queue.pop(0)
        url = song_info['url']
        title = song_info['title']
        voice_client = discord.utils.get(client.voice_clients, guild=message.guild)

        if voice_client and voice_client.is_connected():
            try:
                with yt_dlp.YoutubeDL(YDL_OPTS) as ydl:
                    info = ydl.extract_info(url, download=False)
                    audio_url = info['url']
                
                source = discord.FFmpegPCMAudio(audio_url, **FFMPEG_OPTIONS)
                
                voice_client.play(source, after=lambda e: asyncio.run_coroutine_threadsafe(play_next(message), client.loop))
                
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
    if message.author == client.user:
        return

    content = message.content.lower()
    
    if content.startswith('#dentro'):
        if message.author.voice:
            channel = message.author.voice.channel
            try:
                await channel.connect()
                await message.channel.send(f'✅ Oi, amor!:): **{channel.name}**')
            except discord.ClientException:
                await message.channel.send('Já estou em um canal de voz.')
            except Exception as e:
                await message.channel.send(f'Ocorreu um erro ao conectar: {e}')
        else:
            await message.channel.send('Você precisa estar em um canal de voz para me convidar!')

    elif content.startswith('#play'):
        if not message.author.voice:
            await message.channel.send("Você precisa estar em um canal de voz para tocar música!")
            return

        voice_client = discord.utils.get(client.voice_clients, guild=message.guild)
        if not voice_client or not voice_client.is_connected():
            await message.channel.send("Não estou conectado a um canal de voz. Use `#dentro` primeiro.")
            return

        try:
            url = message.content.split(' ', 1)[1]
            
            with yt_dlp.YoutubeDL(YDL_OPTS) as ydl:
                info = ydl.extract_info(url, download=False)

            if 'entries' in info:
                playlist_entries = info['entries']
                for entry in playlist_entries:
                    if entry and 'webpage_url' in entry and 'title' in entry:
                        song_queue.append({'url': entry['webpage_url'], 'title': entry['title']})
                await message.channel.send(f'🎵 Playlist adicionada! **{len(playlist_entries)}** músicas foram adicionadas à fila.')
            else:
                song_queue.append({'url': url, 'title': info['title']})
                await message.channel.send(f'🎵 Adicionado à fila: **{info["title"]}**')
            
            if not is_playing:
                await play_next(message)

        except IndexError:
            await message.channel.send('Por favor, forneça uma URL do YouTube após o comando `#play`.')
        except Exception as e:
            await message.channel.send(f"Ocorreu um erro ao processar o link: {e}")

    elif content.startswith('#ajuda'):
        # Bloco de ajuda corrigido e verificado
        help_message = """```
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
```"""
        await message.channel.send(help_message)

    elif content.startswith('#fila'):
        if not song_queue:
            await message.channel.send('A fila de músicas está vazia.')
            return

        queue_list = "```"
        for i, song_info in enumerate(song_queue[:10]):
            queue_list += f"{i+1}. {song_info['title']}\n"
        
        if len(song_queue) > 10:
            queue_list += f"\n... e mais {len(song_queue) - 10} música(s)."
        queue_list += "```"
        
        await message.channel.send(f'**Próximas músicas na fila:**\n{queue_list}')

    elif content.startswith('#pular'):
        voice_client = discord.utils.get(client.voice_clients, guild=message.guild)
        if voice_client and voice_client.is_playing():
            voice_client.stop()
            await message.channel.send('⏭️ Música pulada!')
        else:
            await message.channel.send('Não estou tocando nenhuma música no momento para pular.')

    elif content.startswith('#tchau'):
        voice_client = discord.utils.get(client.voice_clients, guild=message.guild)
        if voice_client and voice_client.is_connected():
            song_queue.clear()
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
    print("\n[ERRO] O token fornecido é inválido. Verifique o token nas Environment Variables.")
except Exception as e:
    print(f"\n[ERRO] Ocorreu um erro inesperado: {e}")

