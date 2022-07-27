import json

import discord

from database import Database


class Config:
    def __init__(self, client: discord.Client):
        self.client = client
        self.embeds = {}
        self.texts = {}
        self.delays = {}
        self.values = {}
        self.database = {}
        self.tables = {}
        self.is_debug = True
        self.token = ''
        self.guild = 0
        self.channels = {}
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
            self.roles = jsonfile['debug_roles']
        else:
            self.token = jsonfile['token']
            self.guild = jsonfile['guild']
            self.channels = jsonfile['channels']
            self.roles = jsonfile['roles']

    def get_server(self) -> discord.Guild:
        return self.client.get_guild(self.guild)

    def get_member(self, user_id: int) -> discord.Member:
        return self.get_server().get_member(user_id)

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

    def get_chat_support_role(self) -> discord.Role:
        return self.get_server().get_role(self.roles['chat_support'])

    def get_voice_support_role(self) -> discord.Role:
        return self.get_server().get_role(self.roles['voice_support'])

    def get_video_role(self) -> discord.Role:
        return self.get_server().get_role(self.roles['video'])

    def get_chat(self) -> discord.TextChannel:
        return self.get_server().get_channel(self.channels['chat'])

    def get_bots(self) -> discord.TextChannel:
        return self.get_server().get_channel(self.channels['bots'])

    def get_rules(self) -> discord.TextChannel:
        return self.get_server().get_channel(self.channels['rules'])

    def get_short_rules(self) -> discord.TextChannel:
        return self.get_server().get_channel(self.channels['short_rules'])

    def get_message_log(self) -> discord.TextChannel:
        return self.get_server().get_channel(self.channels['message_log'])

    def get_voice_log(self) -> discord.TextChannel:
        return self.get_server().get_channel(self.channels['voice_log'])

    def get_join_log(self) -> discord.TextChannel:
        return self.get_server().get_channel(self.channels['join_log'])

    def get_leave_log(self) -> discord.TextChannel:
        return self.get_server().get_channel(self.channels['leave_log'])

    def get_voice_support_channel(self) -> discord.VoiceChannel:
        return self.get_server().get_channel(self.channels['voice_support'])

    def get_team_voice_support_channel(self) -> discord.TextChannel:
        return self.get_server().get_channel(self.channels['team_voice_support'])

    @staticmethod
    def has_role(member: discord.Member, role_id: int) -> bool:
        for role in member.roles:
            if role.id == role_id:
                return True
        return False

    @staticmethod
    def is_administrator(member: discord.Member) -> bool:
        for role in member.roles:
            if role.permissions.administrator:
                return True
        return False
