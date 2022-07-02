from datetime import datetime

import discord

from config import Config

months = ['Januar', 'Februar', 'März', 'April', 'Mai', 'Juni', 'Juli', 'August', 'September', 'Oktober', 'November', 'Dezember']


class Module:
    def __init__(self, config: Config):
        self.config = config

    async def on_member_join(self, member: discord.Member) -> None:
        pass

    async def on_member_remove(self, member: discord.Member) -> None:
        pass

    async def on_message(self, message: discord.Message) -> None:
        pass

    async def on_message_delete(self, message: discord.Message) -> None:
        pass

    async def on_message_edit(self, before: discord.Message, after: discord.Message) -> None:
        pass

    async def on_reaction_add(self, reaction: discord.Reaction, member: discord.Member) -> None:
        pass

    async def on_reaction_remove(self, reaction: discord.Reaction, member: discord.Member) -> None:
        pass

    async def on_ready(self) -> None:
        pass

    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState) -> None:
        pass

    @staticmethod
    def new_embed(title: str, color: int) -> discord.Embed:
        embed = discord.Embed(title=title, color=color, timestamp=datetime.utcnow())
        embed.set_footer(text='Melonenbot', icon_url='https://images-ext-1.discordapp.net/external/lZws7G7iw7fozgme7y0bQu-TsswDMAZHwlGVW85F2FU/https/cdn.discordapp.com/avatars/649282521066110986/62c862309170d6d10aecce16fd50cdbb.png')
        return embed

    def embed(self, title: str) -> discord.Embed:
        return self.new_embed(title, 0xECDC34)

    def error_embed(self, title: str) -> discord.Embed:
        return self.new_embed(title, 0xB40404)

    @staticmethod
    def get_readable_date(date: str) -> str:
        y = int(date[:4])
        m = int(date[5:7])
        d = int(date[8:10])
        return str(d) + '. ' + months[m - 1] + ' ' + str(y)

    @staticmethod
    def get_readable_datetime(date: str) -> str:
        return Module.get_readable_date(date) + ', ' + date[11:19]
