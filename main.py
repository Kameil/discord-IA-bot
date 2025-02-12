import google.generativeai as genai
from google.generativeai.types import AsyncGenerateContentResponse
import textwrap
from config import api_key, token
import discord
from discord.ext import commands
from discord import app_commands
import os
import httpx
import base64
import asyncio
from tamga import Tamga

logger = Tamga()

genai.configure(api_key=api_key)

SYSTEM_INSTRUCTION = """
- Seu nome e Rogerio Tech.
- Voce e um bot de discord.
- Voce e engracado e ironico.

voce ira receber mensagens assim: informacoes: mensagem de "nome do usuario": "conteudo da mensagem" ou informacoes: mensagem de "nome do usuario" ativo agora em: "atividade1", "atividade2", "atividad[...]
Voce deve responder o conteudo da mensagem.
"""

model = genai.GenerativeModel("gemini-1.5-flash", system_instruction=SYSTEM_INSTRUCTION)

generation_config = genai.GenerationConfig(
    max_output_tokens=1000,
    temperature=1.0
)

bot = commands.Bot('!!!!!!!!', help_command=None, intents=discord.Intents.all())
rogerioicon = 'https://media.discordapp.net/attachments/1043205236501786654/1225599129032462466/th-1812658305.jpg?ex=6621b722&is=660f4222&hm=a3a77a2aace8af8c5aaab29fad186f0e454723f6932e0daf726643a971b[...]'

chats = {}

@bot.event
async def on_ready():
    logger.success(f'Bot Online Em {bot.user}')
    sync = await bot.tree.sync()
    logger.success(f'{len(sync)} Comandos Foram sincronizados.')

@bot.event
async def on_message(message: discord.Message):
    if not message.author.bot:
        channel_id = str(message.channel.id)
        if f"<@{bot.user.id}>" in message.content or isinstance(message.channel, discord.DMChannel) or bot.user in message.mentions:
            if channel_id not in chats:
                chats[channel_id] = model.start_chat()
            chat = chats[channel_id]

            atividades = [atividade.name for atividade in message.author.activities] if not isinstance(message.channel, discord.DMChannel) and message.author.activities else []

            prompt = f'informacoes: mensagem de "{message.author.name}"'
            if atividades:
                prompt += f" ativo agora em: discord(aqui), {', '.join(atividades)}"
            prompt += f": {message.content.replace(f'<@{bot.user.id}>', 'Rogerio Tech')}"

            async with message.channel.typing():
                images = []
                if message.attachments:
                    async with httpx.AsyncClient() as client:
                        for attachment in message.attachments:
                            if attachment.content_type.startswith("image/"):
                                response = await client.get(attachment.url)
                                image = base64.b64encode(response.content).decode("utf-8")
                                images.append({'mime_type': attachment.content_type, 'data': image})

                if images:
                    prompt = images + [prompt]
                logger.info(f"respondendo mensagem de {message.author.name} em #{message.channel.id}")
                response = chat.send_message(
                    prompt,
                    stream=True,
                    generation_config=generation_config
                )

                message_enviada = await message.reply("...", mention_author=False)
                conteudo = ""  

                for chunk in response:
                    await asyncio.sleep(0.5)
                    if len(conteudo) + len(chunk.text) > 2000:
                        message_enviada = await message.channel.send("z", mention_author=False)
                        conteudo = ""
                    conteudo += chunk.text  
                    await message_enviada.edit(content=conteudo)

    await bot.process_commands(message)

@bot.tree.command(name='analisar', description='descobrir se e desenrolado.')
@app_commands.describe(user="Usuario a ser analisado", mpc="Mensagens por canal. Padrao:100")    
async def Jokenpo(inter: discord.Interaction, user: discord.User, prompt: str=None, mpc: int=100):
    await inter.response.defer()
    if isinstance(inter.channel, discord.DMChannel):
        return await inter.followup.send("Esse comando so pode ser executado em um servidor.")
    try:
        messages = []
        for channel in inter.guild.text_channels:
            async for message in channel.history(limit=mpc):
                if message.author == user:
                    messages.append(f"Mensagem de {user.name} em #{message.channel.name}: {message.content}")
        prompt_probot = f"analise esse usuario com base no seu nome e na sua imagem de perfil e diga se ele e desenrolado ou nao. Nome:{user.name}\n"
        if prompt is not None:
            prompt_probot = "analise um usuario prioridade na analise:" + prompt + f"Nome do usuario: {user.name}, Mensagens do usuario:"
        print(prompt_probot)
        prompt_probot += "\n".join(messages)

        async with httpx.AsyncClient() as client:
            response = await client.get(user.avatar.url)
            if response.status_code == 200:
                avatar = response.content
            else:
                avatar = None

        if avatar:
            response = model.generate_content(
                [{'mime_type': 'image/png', 'data': base64.b64encode(avatar).decode("utf-8")}, prompt_probot],
                generation_config=generation_config
            )
            textos = textwrap.wrap(response.text, 2000)
            for text in textos:
                await inter.followup.send(text)
        else:
            await inter.followup.send("Nao foi possivel obter a imagem do perfil do usuario.")
    except Exception as e:
        await inter.followup.send(f"deu bom nao. Erro: ```python\n{e}\n```")
        logger.error(f"Erro ao analisar usuario em: {inter.guild.name}")

@bot.tree.command(name='resetar', description='Resetar a conversa com o bot no canal atual.')
async def pedra(inter: discord.Interaction):
    try:
        channel_id = str(inter.channel.id)
        if channel_id in chats:
            msgs = len(chats[channel_id].history)
            chats[channel_id] = model.start_chat()
            embed = discord.Embed(title="Conversa resetada", description="A conversa com o bot foi resetada com sucesso.", color=discord.Color.green())
            embed.set_footer(text=f"{msgs} mensagens foram apagadas.")
            await inter.response.send_message(embed=embed)
            logger.success(f"Conversa de id:{inter.channel.id} foi resetada")
        else:
            await inter.response.send_message("Nao ha conversa para resetar.")
    except Exception as e:
        await inter.response.send_message(f"deu bom nao. Erro: ```python\n{e}\n```")
        logger.error("erro ao resetar uma conversa.")


bot.run(token)