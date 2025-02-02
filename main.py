import google.generativeai as genai
import textwrap
from config import api_key, token

genai.configure(api_key=api_key)

model = genai.GenerativeModel("gemini-1.5-flash", system_instruction="Seu Nome È Rogerio Tech e vocè e um bot do discord engracado que responde com respostas engracadas e ironicas")

import discord

from discord.ext import commands
import os
import random
import asyncio
import random

bot = commands.Bot('!!!!!!!!', help_command=None, intents=discord.Intents.all())
rogerioicon = 'https://media.discordapp.net/attachments/1043205236501786654/1225599129032462466/th-1812658305.jpg?ex=6621b722&is=660f4222&hm=a3a77a2aace8af8c5aaab29fad186f0e454723f6932e0daf726643a971bd0ab2&='
@bot.event
async def on_ready():
    print(f'Online {bot.user}')
@bot.event
async def on_message(message: discord.Message):
    if not message.author.bot:
        if f"<@{bot.user.id}>" in message.content:
            async with message.channel.typing():
                response = model.generate_content(
                    message.content.replace("<@1041361324506087555>", "Rogerio Tech"),
                    generation_config = genai.GenerationConfig(
                        max_output_tokens=1000,
                        temperature=0.1
                        )
                        )

                textos = textwrap.wrap(response.text, 2000)
                for texto in textos:
                    await message.channel.send(texto)

    await bot.process_commands(message)


bot.run(token)