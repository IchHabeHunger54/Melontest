import json

import discord


class Config:
    def __init__(self, client: discord.Client):
        self.client = client
        configjson = open('./config.json', 'r', 1)
        jsonfile = json.loads(configjson.read())
        configjson.close()
        self.counter_user = jsonfile['counter_user']
        self.counter_pw = jsonfile['counter_pw']
        self.counter_db = jsonfile['counter_db']
        self.tricks_user = jsonfile['tricks_user']
        self.tricks_pw = jsonfile['tricks_pw']
        self.tricks_db = jsonfile['tricks_db']
        self.host = jsonfile['host']
        self.is_debug = jsonfile['is_debug']
        if self.is_debug:
            self.token = jsonfile['debug_token']
            self.guild_id = jsonfile['debug_guild_id']
            self.test_supporter_id = jsonfile['debug_test_supporter_id']
            self.supporter_id = jsonfile['debug_supporter_id']
            self.test_moderator_id = jsonfile['debug_test_moderator_id']
            self.moderator_id = jsonfile['debug_moderator_id']
            self.voice_support_role_id = jsonfile['debug_voice_support_role_id']
            self.chat_support_role_id = jsonfile['debug_chat_support_role_id']
            self.head_moderator_id = jsonfile['debug_head_moderator_id']
            self.test_administrator_id = jsonfile['debug_test_administrator_id']
            self.chat_id = jsonfile['debug_chat_id']
            self.message_channel_id = jsonfile['debug_message_log_id']
            self.voice_channel_id = jsonfile['debug_voice_log_id']
            self.join_channel_id = jsonfile['debug_join_log_id']
            self.leave_channel_id = jsonfile['debug_leave_log_id']
            self.voice_support_channel_id = jsonfile['debug_voice_support_channel_id']
            self.team_voice_support_channel_id = jsonfile['debug_team_voice_support_channel_id']
            self.rules_id = jsonfile['debug_rules_id']
            self.short_rules_id = jsonfile['debug_short_rules_id']
            self.among_us_delay = jsonfile['debug_among_us_delay']
            self.among_us_delay_offset = jsonfile['debug_among_us_delay_offset']
        else:
            self.token = jsonfile['token']
            self.guild_id = jsonfile['guild_id']
            self.test_supporter_id = jsonfile['test_supporter_id']
            self.supporter_id = jsonfile['supporter_id']
            self.test_moderator_id = jsonfile['test_moderator_id']
            self.moderator_id = jsonfile['moderator_id']
            self.head_moderator_id = jsonfile['head_moderator_id']
            self.test_administrator_id = jsonfile['test_administrator_id']
            self.voice_support_role_id = jsonfile['voice_support_role_id']
            self.chat_support_role_id = jsonfile['chat_support_role_id']
            self.chat_id = jsonfile['chat_id']
            self.message_channel_id = jsonfile['message_log_id']
            self.voice_channel_id = jsonfile['voice_log_id']
            self.join_channel_id = jsonfile['join_log_id']
            self.leave_channel_id = jsonfile['leave_log_id']
            self.voice_support_channel_id = jsonfile['voice_support_channel_id']
            self.team_voice_support_channel_id = jsonfile['team_voice_support_channel_id']
            self.rules_id = jsonfile['rules_id']
            self.short_rules_id = jsonfile['short_rules_id']
            self.among_us_delay = jsonfile['among_us_delay']
            self.among_us_delay_offset = jsonfile['among_us_delay_offset']
        self.flo_1_emote = jsonfile['flo_1_emote']
        self.flo_2_emote = jsonfile['flo_2_emote']
        self.flo_3_emote = jsonfile['flo_3_emote']
        self.among_us_1_emote = jsonfile['among_us_1_emote']
        self.among_us_2_emote = jsonfile['among_us_2_emote']
        self.among_us_3_emote = jsonfile['among_us_3_emote']
        self.among_us_4_emote = jsonfile['among_us_4_emote']

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

    def is_test_administrator_or_higher(self, member: discord.Member) -> bool:
        return self.has_role(member, self.test_administrator_id) or self.is_administrator(member)

    def is_head_moderator_or_higher(self, member: discord.Member) -> bool:
        return self.has_role(member, self.head_moderator_id) or self.is_test_administrator_or_higher(member)

    def is_moderator_or_higher(self, member: discord.Member) -> bool:
        return self.has_role(member, self.moderator_id) or self.is_head_moderator_or_higher(member)

    def is_test_moderator_or_higher(self, member: discord.Member) -> bool:
        return self.has_role(member, self.test_moderator_id) or self.is_moderator_or_higher(member)

    def is_supporter_or_higher(self, member: discord.Member) -> bool:
        return self.has_role(member, self.supporter_id) or self.is_test_moderator_or_higher(member)

    def is_test_supporter_or_higher(self, member: discord.Member) -> bool:
        return self.has_role(member, self.head_moderator_id) or self.is_supporter_or_higher(member)

    def is_team(self, member: discord.Member) -> bool:
        return self.is_test_supporter_or_higher(member)

    def get_server(self) -> discord.Guild:
        return self.client.get_guild(self.guild_id)

    def get_chat_support_role(self) -> discord.Role:
        return self.get_server().get_role(self.chat_support_role_id)

    def get_voice_support_role(self) -> discord.Role:
        return self.get_server().get_role(self.voice_support_role_id)

    def get_chat(self) -> discord.TextChannel:
        return self.get_server().get_channel(self.chat_id)

    def get_message_log(self) -> discord.TextChannel:
        return self.get_server().get_channel(self.message_channel_id)

    def get_voice_log(self) -> discord.TextChannel:
        return self.get_server().get_channel(self.voice_channel_id)

    def get_join_log(self) -> discord.TextChannel:
        return self.get_server().get_channel(self.join_channel_id)

    def get_leave_log(self) -> discord.TextChannel:
        return self.get_server().get_channel(self.leave_channel_id)

    def get_voice_support_channel(self) -> discord.VoiceChannel:
        return self.get_server().get_channel(self.voice_support_channel_id)

    def get_team_voice_support_channel(self) -> discord.TextChannel:
        return self.get_server().get_channel(self.team_voice_support_channel_id)

    def get_member(self, user_id: int) -> discord.Member:
        return self.get_server().get_member(user_id)
