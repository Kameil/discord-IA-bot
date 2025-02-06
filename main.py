import google.generativeai as genai
import textwrap
from config import api_key, token

genai.configure(api_key=api_key)

model = genai.GenerativeModel("gemini-1.5-flash", system_instruction="""
- Seu nome e Rogerio Tech.
- Voce e um bot de discord.
- Voce e engracado e ironico.

voce ira receber mensagens assim: informacoes: mensagem de "nome do usuario": "conteudo da mensagem" ou informacoes: mensagem de "nome do usuario" ativo agora em: "atividade1", "atividade2", "atividade3": "conteudo da mensagem"
Voce deve responder o conteudo da mensagem.

"""
)

generation_config = genai.GenerationConfig(
                        max_output_tokens=1000,
                        temperature=0.5
                        )

import discord

from discord.ext import commands
from discord import app_commands

import os
import random
import asyncio
import random

bot = commands.Bot('!!!!!!!!', help_command=None, intents=discord.Intents.all())
rogerioicon = 'https://media.discordapp.net/attachments/1043205236501786654/1225599129032462466/th-1812658305.jpg?ex=6621b722&is=660f4222&hm=a3a77a2aace8af8c5aaab29fad186f0e454723f6932e0daf726643a971bd0ab2&='
@bot.event
async def on_ready():
    print(f'Online {bot.user}')
    sync = await bot.tree.sync()
    print(f'{len(sync)} Comandos Foram sincronizados.')


import httpx
import base64

chats = {}

@bot.event
async def on_message(message: discord.Message):
    global chats
    if not message.author.bot:
        if f"<@{bot.user.id}>" in message.content or isinstance(message.channel, discord.DMChannel):
            if not chats.get(str(message.channel.id)):
                chats[str(message.channel.id)] = model.start_chat()
            chat = chats[str(message.channel.id)]
            atividades = []
            if not isinstance(message.channel, discord.DMChannel):
                if message.author.activities:
                    print(message.author.activities)
                    atividades = []
                    for atividade in message.author.activities:
                        atividades.append(atividade.name)
            prompt = "informacoes: mensagem de " + '"' + message.author.name + '"'
            if len(atividades) > 0:
                prompt += " ativo agora em: discord(aqui), " + ", ".join(atividades)
                print(prompt)
            prompt +=  ": " + message.content.replace("<@1041361324506087555>", "Rogerio Tech")
            async with message.channel.typing():
                images = []
                count = 1
                if message.attachments:
                    for attachment in message.attachments:
                        if attachment.content_type.startswith("image/"):
                            async with httpx.AsyncClient() as client:
                                response = await client.get(attachment.url)
                                image = base64.b64encode(response.content).decode("utf-8")
                                images.append({'mime_type': attachment.content_type, 'data': image})
                                count += 1
                if len(images) > 0:
                    prompt = [image for image in images] + [prompt]
                
                response = chat.send_message(
                    prompt,
                    stream = True,
                    generation_config = generation_config
                        )

                # textos = textwrap.wrap(response.text, 2000)
                message_enviada = await message.reply("...", mention_author=False)
                conteudo = ""  

                for chunk in response:
                    if len(conteudo) + len(chunk.text) > 2000:
                        message_enviada = await message.channel.send("z", mention_author=False)
                        conteudo = ""
                    conteudo += chunk.text  
                    await message_enviada.edit(content=conteudo) 


    await bot.process_commands(message)


@bot.tree.command(name='analisar', description='descobrir se e desenrolado.')
@app_commands.describe(user="Usuario a ser analisado", mpc="Mensagens por canal. Padrao:100")	
async def Jokenpo(inter: discord.Interaction, user: discord.User, mpc: int=100):
    await inter.response.defer()
    if isinstance(inter.channel, discord.DMChannel):
        return await inter.followup.send("Esse comando so pode ser executado em um servidor.")
    try:


        messages = []
        for channel in inter.guild.text_channels:
            async for message in channel.history(limit=mpc):
                if message.author == user:
                    messages.append("Mensagem de " + user.name + f" em #{message.channel.name}: " + message.content)

        prompt = "analise esse usuario com base no seu nome e na sua imagem de perfil e diga se ele e desenrolado ou nao. Nome:" + user.name
        prompt += "/n".join(messages)
        async with httpx.AsyncClient() as client:
            response = await client.get(user.avatar.url)
            if response.status_code == 200:
                print(user.avatar.url)
            
                print(response.status_code)
            avatar = response.content
        response = model.generate_content(
        [{'mime_type': 'image/png', 'data': base64.b64encode(avatar).decode("utf-8")}, prompt],
        generation_config=generation_config
    )

        await inter.followup.send(response.text)
    except Exception as e:	
        await inter.followup.send(f"deu bom nao. Erro: ```python\n{e}\n```")


bot.run(token)