import json
from typing import Optional

import discord

from database import Database


class Config:
    def __init__(self, client: discord.Client):
        self.client = client
        self.embeds = {}
        self.texts = {}
        self.delays = {}
        self.values = {}
        self.database = None
        self.tables = {}
        self.is_debug = True
        self.token = ''
        self.guild = 0
        self.channels = {}
        self.categories = {}
        self.roles = {}
        self.load()

    def load(self):
        with open('./config.json', encoding='utf-8') as file:
            jsonfile = json.loads(file.read())
        self.embeds = jsonfile['embeds']
        self.texts = jsonfile['texts']
        self.delays = jsonfile['delays']
        self.values = jsonfile['values']
        self.database = Database(jsonfile['database'])
        self.is_debug = jsonfile['is_debug']
        if self.is_debug:
            self.token = jsonfile['debug_token']
            self.guild = jsonfile['debug_guild']
            self.channels = jsonfile['debug_channels']
            self.categories = jsonfile['debug_categories']
            self.roles = jsonfile['debug_roles']
        else:
            self.token = jsonfile['token']
            self.guild = jsonfile['guild']
            self.channels = jsonfile['channels']
            self.categories = jsonfile['categories']
            self.roles = jsonfile['roles']

    def server(self) -> discord.Guild:
        return self.client.get_guild(self.guild)

    def member(self, user_id: int) -> discord.Member:
        return self.server().get_member(user_id)

    def role(self, role_id: int) -> discord.Role:
        return self.server().get_role(role_id)

    def text_channel(self, channel_id: int) -> Optional[discord.TextChannel]:
        channel = self.server().get_channel(channel_id)
        return channel if isinstance(channel, discord.TextChannel) else None

    def voice_channel(self, channel_id: int) -> Optional[discord.VoiceChannel]:
        channel = self.server().get_channel(channel_id)
        return channel if isinstance(channel, discord.VoiceChannel) else None

    def category(self, category_id: str) -> discord.CategoryChannel:
        category = None
        for c in self.server().categories:
            if c.id == self.categories[category_id]:
                category = c
        return category

    def is_test_administrator_or_higher(self, member: discord.Member) -> bool:
        return self.has_role(member, self.roles['test_administrator']) or self.is_administrator(member)

    def is_head_moderator_or_higher(self, member: discord.Member) -> bool:
        return self.has_role(member, self.roles['head_moderator']) or self.is_test_administrator_or_higher(member)

    def is_moderator_or_higher(self, member: discord.Member) -> bool:
        return self.has_role(member, self.roles['moderator']) or self.is_head_moderator_or_higher(member)

    def is_test_moderator_or_higher(self, member: discord.Member) -> bool:
        return self.has_role(member, self.roles['test_moderator']) or self.is_moderator_or_higher(member)

    def is_supporter_or_higher(self, member: discord.Member) -> bool:
        return self.has_role(member, self.roles['supporter']) or self.is_test_moderator_or_higher(member)

    def is_test_supporter_or_higher(self, member: discord.Member) -> bool:
        return self.has_role(member, self.roles['test_supporter']) or self.is_supporter_or_higher(member)

    def is_team(self, member: discord.Member) -> bool:
        return self.is_test_supporter_or_higher(member)

    def default_role(self) -> discord.Role:
        return self.server().get_role(self.roles['default'])

    def premium_role(self) -> discord.Role:
        return self.server().get_role(self.roles['premium'])

    def special_role(self) -> discord.Role:
        return self.server().get_role(self.roles['special'])

    def chat_support_role(self) -> discord.Role:
        return self.server().get_role(self.roles['chat_support'])

    def voice_support_role(self) -> discord.Role:
        return self.server().get_role(self.roles['voice_support'])

    def video_role(self) -> discord.Role:
        return self.server().get_role(self.roles['video'])

    def muted_role(self) -> discord.Role:
        return self.server().get_role(self.roles['muted'])

    def chat(self) -> discord.TextChannel:
        return self.text_channel(self.channels['chat'])

    def bots(self) -> discord.TextChannel:
        return self.text_channel(self.channels['bots'])

    def rules(self) -> discord.TextChannel:
        return self.text_channel(self.channels['rules'])

    def short_rules(self) -> discord.TextChannel:
        return self.text_channel(self.channels['short_rules'])

    def message_log(self) -> discord.TextChannel:
        return self.text_channel(self.channels['message_log'])

    def voice_log(self) -> discord.TextChannel:
        return self.text_channel(self.channels['voice_log'])

    def join_log(self) -> discord.TextChannel:
        return self.text_channel(self.channels['join_log'])

    def leave_log(self) -> discord.TextChannel:
        return self.text_channel(self.channels['leave_log'])

    def voice_support(self) -> discord.VoiceChannel:
        return self.voice_channel(self.channels['voice_support'])

    def team_voice_support(self) -> discord.TextChannel:
        return self.text_channel(self.channels['team_voice_support'])

    def tickets(self) -> discord.TextChannel:
        return self.text_channel(self.channels['tickets'])

    def afk(self) -> discord.VoiceChannel:
        return self.voice_channel(self.channels['afk'])

    def voice_join(self) -> discord.VoiceChannel:
        return self.voice_channel(self.channels['voice_join'])

    def voice_move(self) -> discord.VoiceChannel:
        return self.voice_channel(self.channels['voice_move'])

    def tickets_category(self) -> discord.CategoryChannel:
        return self.category('tickets')

    def voice_category(self) -> discord.CategoryChannel:
        return self.category('voice')

    @staticmethod
    def has_role(member: discord.Member, role_id: int) -> bool:
        return any(role.id == role_id for role in member.roles)

    @staticmethod
    def is_administrator(member: discord.Member) -> bool:
        return any(role.permissions.administrator for role in member.roles)
