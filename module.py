import json
from datetime import datetime
from typing import Optional

import psycopg2
from discord import *
from discord.ext import tasks


class Config:
    def __init__(self, client: Client):
        self.client = client
        self.modules = []
        self.embeds = {}
        self.texts = {}
        self.intervals = {}
        self.values = {}
        self.database = None
        self.is_debug = True
        self.token = ''
        self.guild = 0
        self.channels = {}
        self.categories = {}
        self.roles = {}

    def load(self):
        with open('./config.json', encoding='utf-8') as file:
            jsonfile = json.loads(file.read())
        self.embeds = jsonfile['embeds']
        self.texts = jsonfile['texts']
        self.intervals = jsonfile['intervals']
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
        for m in self.modules:
            m.load()


class Module:
    def __init__(self, config: Config, name: str):
        self.config = config
        self.name = name
        self.database = None
        self.text = {}
        self.interval = None
        self.values = {}

    def load(self) -> None:
        self.database = self.config.database
        try:
            self.text = self.config.texts[self.name]
            if self.text is None:
                self.text = {}
        except (KeyError, ValueError, TypeError):
            pass
        try:
            self.values = self.config.values[self.name]
            if self.values is None:
                self.values = {}
        except (KeyError, ValueError, TypeError):
            pass
        try:
            self.interval = self.config.intervals[self.name]
            if self.interval is not None:
                self.run_schedule.change_interval(seconds=self.get_interval())
        except (KeyError, ValueError, TypeError):
            pass

    async def on_member_join(self, member: Member) -> None:
        pass

    async def on_member_remove(self, member: Member) -> None:
        pass

    async def on_member_update(self, before: Member, after: Member) -> None:
        pass

    async def on_user_update(self, before: User, after: User) -> None:
        pass

    async def on_message(self, message: Message) -> None:
        pass

    async def on_message_delete(self, message: Message) -> None:
        pass

    async def on_message_edit(self, before: Message, after: Message) -> None:
        pass

    async def on_reaction_add(self, reaction: Reaction, member: Member) -> None:
        pass

    async def on_reaction_remove(self, reaction: Reaction, member: Member) -> None:
        pass

    async def on_ready(self) -> None:
        self.run_schedule.start()

    async def on_voice_state_update(self, member: Member, before: VoiceState, after: VoiceState) -> None:
        pass

    @tasks.loop(seconds=1)
    async def run_schedule(self) -> None:
        pass

    def get_interval(self) -> int:
        return self.interval

    def bot_user(self) -> ClientUser:
        return self.config.client.user

    def server(self) -> Guild:
        return self.config.client.get_guild(self.config.guild)

    def member(self, user_id: int) -> Member:
        return self.server().get_member(user_id)

    def role(self, role_id: int) -> Role:
        return self.server().get_role(role_id)

    def text_channel(self, channel_id: int) -> Optional[TextChannel]:
        channel = self.server().get_channel(channel_id)
        return channel if isinstance(channel, TextChannel) else None

    def voice_channel(self, channel_id: int) -> Optional[VoiceChannel]:
        channel = self.server().get_channel(channel_id)
        return channel if isinstance(channel, VoiceChannel) else None

    def category(self, category_id: str) -> Optional[CategoryChannel]:
        for c in self.server().categories:
            if c.id == self.config.categories[category_id]:
                return c
        return None

    def default_role(self) -> Role:
        return self.role(self.config.roles['default'])

    def premium_role(self) -> Role:
        return self.role(self.config.roles['premium'])

    def special_role(self) -> Role:
        return self.role(self.config.roles['special'])

    def special_requirement_role(self) -> Role:
        return self.role(self.config.roles['special_requirement'])

    def prank_mute_requirement_role(self) -> Role:
        return self.role(self.config.roles['prank_mute_requirement'])

    def vip_role(self) -> Role:
        return self.role(self.config.roles['vip'])

    def builder_role(self) -> Role:
        return self.role(self.config.roles['builder'])

    def test_supporter(self) -> Role:
        return self.role(self.config.roles['test_supporter'])

    def supporter(self) -> Role:
        return self.role(self.config.roles['supporter'])

    def moderator(self) -> Role:
        return self.role(self.config.roles['moderator'])

    def head_moderator(self) -> Role:
        return self.role(self.config.roles['head_moderator'])

    def test_administrator(self) -> Role:
        return self.role(self.config.roles['test_administrator'])

    def chat_support_role(self) -> Role:
        return self.role(self.config.roles['chat_support'])

    def voice_support_role(self) -> Role:
        return self.role(self.config.roles['voice_support'])

    def video_role(self) -> Role:
        return self.role(self.config.roles['video'])

    def muted_role(self) -> Role:
        return self.role(self.config.roles['muted'])

    def chat(self) -> TextChannel:
        return self.text_channel(self.config.channels['chat'])

    def bots(self) -> TextChannel:
        return self.text_channel(self.config.channels['bots'])

    def rules(self) -> TextChannel:
        return self.text_channel(self.config.channels['rules'])

    def short_rules(self) -> TextChannel:
        return self.text_channel(self.config.channels['short_rules'])

    def moderation_log(self) -> TextChannel:
        return self.text_channel(self.config.channels['moderation_log'])

    def member_log(self) -> TextChannel:
        return self.text_channel(self.config.channels['member_log'])

    def message_log(self) -> TextChannel:
        return self.text_channel(self.config.channels['message_log'])

    def voice_log(self) -> TextChannel:
        return self.text_channel(self.config.channels['voice_log'])

    def join_log(self) -> TextChannel:
        return self.text_channel(self.config.channels['join_log'])

    def leave_log(self) -> TextChannel:
        return self.text_channel(self.config.channels['leave_log'])

    def voice_support(self) -> VoiceChannel:
        return self.voice_channel(self.config.channels['voice_support'])

    def team_voice_support(self) -> TextChannel:
        return self.text_channel(self.config.channels['team_voice_support'])

    def tickets(self) -> TextChannel:
        return self.text_channel(self.config.channels['tickets'])

    def afk(self) -> VoiceChannel:
        return self.voice_channel(self.config.channels['afk'])

    def voice_join(self) -> VoiceChannel:
        return self.voice_channel(self.config.channels['voice_join'])

    def voice_move(self) -> VoiceChannel:
        return self.voice_channel(self.config.channels['voice_move'])

    def tickets_category(self) -> CategoryChannel:
        return self.category('tickets')

    def voice_category(self) -> CategoryChannel:
        return self.category('voice')

    def is_team(self, member: Member) -> bool:
        return self.is_test_supporter_or_higher(member)

    def is_test_supporter_or_higher(self, member: Member) -> bool:
        return self.has_role(member, self.test_supporter()) or self.is_supporter_or_higher(member)

    def is_supporter_or_higher(self, member: Member) -> bool:
        return self.has_role(member, self.supporter()) or self.is_moderator_or_higher(member)

    def is_moderator_or_higher(self, member: Member) -> bool:
        return self.has_role(member, self.moderator()) or self.is_head_moderator_or_higher(member)

    def is_head_moderator_or_higher(self, member: Member) -> bool:
        return self.has_role(member, self.head_moderator()) or self.is_test_administrator_or_higher(member)

    def is_test_administrator_or_higher(self, member: Member) -> bool:
        return self.has_role(member, self.test_administrator()) or self.is_administrator(member)

    def new_embed(self, title: str, color: int) -> Embed:
        embed = Embed(title=title, color=color, timestamp=datetime.utcnow())
        embed.set_footer(text=self.config.embeds['text'], icon_url=self.config.embeds['icon'])
        return embed

    def embed(self, title: str) -> Embed:
        return self.new_embed(title, self.config.embeds['color'])

    def error_embed(self, title: str) -> Embed:
        return self.new_embed(title, self.config.embeds['error_color'])

    def readable_date(self, date: str) -> str:
        return '\u200b' + date[8:10] + '. ' + self.config.texts['months'][int(date[5:7]) - 1] + ' ' + date[:4]

    def readable_datetime(self, date: str) -> str:
        return self.readable_date(date) + ', ' + date[11:19]

    async def member_from_id(self, mention_or_id: str, message: Message) -> Optional[Member]:
        if mention_or_id.startswith('<@') and mention_or_id.endswith('>'):
            mention_or_id = mention_or_id[2:-1]
        try:
            userid = int(mention_or_id)
        except ValueError:
            await self.error_and_delete(message, self.config.texts['invalid'])
            return None
        return self.member(userid)

    async def team_member_from_id(self, mention_or_id: str, message: Message) -> Optional[Member]:
        member = await self.member_from_id(mention_or_id, message)
        if member is None:
            return None
        if not self.is_team(member):
            await self.error_and_delete(message, self.config.texts['only_team'])
            return None
        return member

    async def non_team_member_from_id(self, mention_or_id: str, message: Message) -> Optional[Member]:
        member = await self.member_from_id(mention_or_id, message)
        if member is None:
            return None
        if self.is_team(member):
            await self.error_and_delete(message, self.config.texts['no_team'])
            return None
        return member

    async def error_and_delete(self, message: Message, text: str) -> None:
        await message.channel.send(text, delete_after=self.config.values['delete_after'])
        await message.delete()

    @staticmethod
    def has_role(member: Member, role: Role) -> bool:
        return any(r.id == role.id for r in member.roles)

    @staticmethod
    def is_administrator(member: Member) -> bool:
        return any(role.permissions.administrator for role in member.roles)

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


class Database:
    def __init__(self, database: dict):
        self.username = database['username']
        self.password = database['password']
        self.hostname = database['hostname']
        self.database = database['database']
        self.port = database['port']

    def execute(self, query: str, *args) -> list[tuple]:
        try:
            with psycopg2.connect(user=self.username, password=self.password, host=self.hostname, database=self.database, port=self.port) as connection:
                with connection.cursor() as cursor:
                    cursor.execute(query, args)
                    try:
                        result = cursor.fetchall()
                    except psycopg2.ProgrammingError:
                        result = None
                    connection.commit()
                    return result
        except (Exception, psycopg2.DatabaseError) as e:
            print('Caught SQL Error:', e)
