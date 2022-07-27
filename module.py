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

    async def get_member_from_id_or_mention(self, mention: str, message: discord.Message):
        if mention.startswith('<@') and mention.endswith('>'):
            mention = mention[2:-1]
        try:
            userid = int(mention)
        except ValueError:
            await message.channel.send(self.config.texts['invalid'], delete_after=self.config.values['delete_after'])
            await message.delete(delay=self.config.values['delete_after'])
            return None
        return self.config.get_member(userid)

    async def get_team_member_from_id_or_mention(self, mention: str, message: discord.Message):
        member = await self.get_member_from_id_or_mention(mention, message)
        if member is None:
            return None
        if not self.config.is_team(member):
            await message.channel.send(self.config.texts['only_team'], delete_after=self.config.values['delete_after'])
            await message.delete(delay=self.config.values['delete_after'])
            return None
        return member

    async def get_non_team_member_from_id_or_mention(self, mention: str, message: discord.Message):
        member = await self.get_member_from_id_or_mention(mention, message)
        if member is None:
            return None
        if self.config.is_team(member):
            await message.channel.send(self.config.texts['no_team'], delete_after=self.config.values['delete_after'])
            await message.delete(delay=self.config.values['delete_after'])
            return None
        return member

    @staticmethod
    def get_duration(duration: str):
        duration = duration.lower()
        if duration.endswith('s'):
            factor = 1
        elif duration.endswith('m'):
            factor = 60
        elif duration.endswith('h'):
            factor = 3600
        elif duration.endswith('d'):
            factor = 86400
        elif duration.endswith('w'):
            factor = 604800
        else:
            return None
        try:
            base = int(duration[:-1])
        except ValueError:
            return None
        return base * factor
