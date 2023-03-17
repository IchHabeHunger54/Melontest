from datetime import datetime
from typing import Optional

import discord
from discord.ext import tasks

from config import Config


class Module:
    def __init__(self, config: Config, interval: int = None):
        self.config = config
        self.interval = interval

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
        if self.interval is not None:
            self.update_interval()
            self.run_schedule.start()

    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState) -> None:
        pass

    @tasks.loop(seconds=1)
    async def run_schedule(self) -> None:
        pass

    def update_interval(self) -> None:
        self.run_schedule.change_interval(seconds=self.interval)

    def new_embed(self, title: str, color: int) -> discord.Embed:
        embed = discord.Embed(title=title, color=color, timestamp=datetime.utcnow())
        embed.set_footer(text=self.config.embeds['text'], icon_url=self.config.embeds['icon'])
        return embed

    def embed(self, title: str) -> discord.Embed:
        return self.new_embed(title, self.config.embeds['color'])

    def error_embed(self, title: str) -> discord.Embed:
        return self.new_embed(title, self.config.embeds['error_color'])

    def get_readable_date(self, date: str) -> str:
        return date[8:10] + '. ' + self.config.texts['months'][int(date[5:7]) - 1] + ' ' + date[:4]

    def get_readable_datetime(self, date: str) -> str:
        return self.get_readable_date(date) + ', ' + date[11:19]

    async def get_member_from_id_or_mention(self, mention: str, message: discord.Message) -> Optional[discord.Member]:
        if mention.startswith('<@') and mention.endswith('>'):
            mention = mention[2:-1]
        try:
            userid = int(mention)
        except ValueError:
            await self.error_and_delete(message, self.config.texts['invalid'])
            return None
        return self.config.member(userid)

    async def get_team_member_from_id_or_mention(self, mention: str, message: discord.Message) -> Optional[discord.Member]:
        member = await self.get_member_from_id_or_mention(mention, message)
        if member is None:
            return None
        if not self.config.is_team(member):
            await self.error_and_delete(message, self.config.texts['only_team'])
            return None
        return member

    async def get_non_team_member_from_id_or_mention(self, mention: str, message: discord.Message) -> Optional[discord.Member]:
        member = await self.get_member_from_id_or_mention(mention, message)
        if member is None:
            return None
        if self.config.is_team(member):
            await self.error_and_delete(message, self.config.texts['no_team'])
            return None
        return member

    async def error_and_delete(self, message: discord.Message, text: str) -> None:
        await message.channel.send(text, delete_after=self.config.values['delete_after'])
        await message.delete()

    @staticmethod
    def get_duration(duration: str) -> Optional[int]:
        duration = duration.lower()
        factors = {'s': 1, 'm': 60, 'h': 3600, 'd': 86400, 'w': 604800}
        if duration[-1] in factors.keys():
            factor = factors[duration[-1]]
        else:
            return None
        try:
            base = int(duration[:-1])
        except ValueError:
            return None
        return base * factor
