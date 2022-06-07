from datetime import datetime

import discord

from config import Config
from database import Database


class Module:
    def __init__(self, config: Config, database: Database):
        self.config = config
        self.database = database

    def on_member_join(self, member: discord.Member) -> None:
        pass

    def on_member_remove(self, member: discord.Member) -> None:
        pass

    def on_message(self, message: discord.Message) -> None:
        pass

    def on_message_delete(self, message: discord.Message) -> None:
        pass

    def on_message_edit(self, before: discord.Message, after: discord.Message) -> None:
        pass

    def on_ready(self) -> None:
        pass

    def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState) -> None:
        pass

    @staticmethod
    def new_embed(title: str, color: int) -> discord.Embed:
        embed = discord.Embed(title=title, color=color, timestamp=datetime.now())
        embed.set_footer(text='Melonenbot', icon_url='https://images-ext-1.discordapp.net/external/lZws7G7iw7fozgme7y0bQu-TsswDMAZHwlGVW85F2FU/https/cdn.discordapp.com/avatars/649282521066110986/62c862309170d6d10aecce16fd50cdbb.png')
        return embed

    def embed(self, title: str) -> discord.Embed:
        return self.new_embed(title, 0xECDC34)

    def error_embed(self, title: str) -> discord.Embed:
        return self.new_embed(title, 0xB40404)
