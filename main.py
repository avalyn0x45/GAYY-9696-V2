'''
Copyright (C) 2025  Avalyn Baldyga
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as
published by the Free Software Foundation, either version 2 of the
License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
'''

import discord
import sqlite3
import random
import os
import re
import json
import atexit
import sys
from PIL import Image, ImageDraw, ImageFont
from typing import Optional
from collections.abc import Callable,Awaitable,Mapping

ResponseFunction = Callable[[discord.Message], Optional[str]]

class Bot:
    token: str
    client: discord.Bot
    regex_responses: list[tuple[re.Pattern, ResponseFunction]] = []
    def __init__(self):
        self.client = discord.Bot(intents = discord.Intents.all())
        self.onmsg = self.regexd(".")
        @self.client.event
        async def on_message(message):
            if message.author == self.client.user:
                return
            for regex, response in self.regex_responses:
                if regex.match(message.content.lower()):
                    resp = response(message)
                    if resp == 69:
                        return
                    if resp:
                        await message.channel.send(resp)
    def start(self, token):
        self.token = token
        self.client.run(token)
    """regex function decorator"""
    def regexd(self, regex: str):
        def deco(func: ResponseFunction):
            self.regex_responses.append((re.compile(regex), func))
            return func
        return deco
    def regex(self, regex: str, resp: str):
        self.regexd(regex)(lambda _:resp)

bot = Bot()
config = json.load(open("config.json",'r'))
atexit.register(lambda: json.dump(config, open("config.json", 'w'), indent = 4))
font = ImageFont.truetype('resources/font.ttf', 20)

@bot.onmsg
def blocklists(message):
    if message.channel.id in config["disabled_channels"]:
        return 69
    if message.author.id in config["disabled_users"]:
        return 69

for regex, resp in config["responses"].items():
    bot.regex(regex,resp)

@bot.onmsg
def randomrsp(_):
    if random.randint(1,1000) / 1000 < config["random_response_prob"]: #random val 0-1 > probability 0-1
        return random.choice(config["random_responses"])

@bot.onmsg
def on_ping(message):
    if bot.client.user.mentioned_in(message):
        if message.author.id == 936030536021999637:
            return "You are such an egg."
        return random.choice(config["on_ping_msgs"])

@bot.client.command(description="make bot ignore you")
async def disable(ctx):
    config["disabled_users"].append(ctx.author.id)
    json.dump(config, open("config.json", 'w'), indent = 4)
    await ctx.respond("ok")

@bot.client.command(description="make bot stop ignoring you")
async def enable(ctx):
    config["disabled_users"].remove(ctx.author.id)
    json.dump(config, open("config.json", 'w'), indent = 4)
    await ctx.respond("ok")


@bot.client.command(description="make bot ignore this channel")
async def disablechannel(ctx):
    if ctx.channel.permissions_for(ctx.author).manage_channels or ctx.author.id == 561328826123026453:
        config["disabled_channels"].append(ctx.channel.id)
        json.dump(config, open("config.json", 'w'), indent = 4)
        await ctx.respond("ok")
    else:
        await ctx.respond("https://www.youtube.com/watch?v=Q6USlUVshBM")

@bot.client.command(description="make bot stop ignoring this channel")
async def enablechannel(ctx):
    if ctx.channel.permissions_for(ctx.author).manage_channels or ctx.author.id == 561328826123026453:
        config["disabled_channels"].remove(ctx.channel.id)
        json.dump(config, open("config.json", 'w'), indent = 4)
        await ctx.respond("ok")
    else:
        await ctx.respond("https://www.youtube.com/watch?v=Q6USlUVshBM")

flags = ["Gay", "Lesbian", "Rainbow", "Progress", "Bi", "Pan", "Arizona", "Trans"]
@bot.client.command(description="forge a license :3")
async def license(ctx, 
                    flag: discord.Option(discord.SlashCommandOptionType.string, "what pride flag?", choices=flags), 
                    pronouns: discord.Option(discord.SlashCommandOptionType.string, "what are your pronouns?"),
                ):
    global font
    assert flag in flags
    base = Image.open("resources/base.png")
    flagimg = Image.open(f"resources/{flag}.png")
    base.paste(flagimg, (0,0), flagimg)
    i1 = ImageDraw.Draw(base)
    i1.text((368, 155), ctx.author.display_name, font=font, fill=(0, 0, 0))
    i1.text((400, 190), pronouns, font=font, fill=(0, 0, 0))
    base.save('temp.png')
    with open("temp.png", "rb") as f:
        image = discord.File(f) 
        await ctx.respond(file=image)

predict = bot.client.create_group("predict", "Predict if someone might be a pretty little fruitcake :3")

@predict.command(description="predict whether or not someone is totally an egg or not :3")
async def egg(ctx, user: discord.Option(discord.SlashCommandOptionType.user , "what user?")):
    rng = random.randint(1,100)
    if user.id == 936030536021999637:
        rng += 100
    if random.randint(1,10) == 1:
        rng*=user.id
    embed = discord.Embed(
        title=f"{rng}%",
        description=f"<@{user.id}> is {rng}% an egg.",
        color=discord.Colour.blurple(),
    )
    await ctx.respond("", embed=embed)

async def reload(ctx):
    await ctx.respond("on it, boss.")
    os.execl(sys.executable, sys.executable, *sys.argv) 

@bot.client.command(description="add resp")
async def addresp(
                ctx, 
                regex: discord.Option(discord.SlashCommandOptionType.string, "regex"),
                response: discord.Option(discord.SlashCommandOptionType.string, "response")
            ):
    if ctx.author.id != config["owner"]:
        await ctx.respond("nope")
        return
    config["responses"][regex] = response
    json.dump(config, open("config.json", 'w'), indent = 4)
    await reload(ctx)

bot.client.command(description="reload config.json")(reload)

if __name__ == "__main__":
    bot.start(os.environ['gayytoken'])
