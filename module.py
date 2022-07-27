from datetime import datetime

import discord

from config import Config


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

    def new_embed(self, title: str, color: int) -> discord.Embed:
        embed = discord.Embed(title=title, color=color, timestamp=datetime.utcnow())
        embed.set_footer(text=self.config.embeds['text'], icon_url=self.config.embeds['icon'])
        return embed

    def embed(self, title: str) -> discord.Embed:
        return self.new_embed(title, self.config.embeds['color'])

    def error_embed(self, title: str) -> discord.Embed:
        return self.new_embed(title, self.config.embeds['error_color'])

    def get_readable_date(self, date: str) -> str:
        y = int(date[:4])
        m = int(date[5:7])
        d = int(date[8:10])
        return str(d) + '. ' + self.config.texts['months'][m - 1] + ' ' + str(y)

    def get_readable_datetime(self, date: str) -> str:
        return self.get_readable_date(date) + ', ' + date[11:19]
