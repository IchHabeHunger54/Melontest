import asyncio
import random
from datetime import datetime, timedelta, timezone

import emoji as demoji
from discord import *
from discord.ext import tasks

from module import Config, Module


class AmongUs(Module):
    def __init__(self, config: Config, name: str):
        super().__init__(config, name)
        self.message = None
        self.reactions = {}
        self.order = []
        self.impostor = None
        self.crewmate1 = None
        self.crewmate2 = None
        self.votes = [0, 0, 0]
        self.first = True
        self.emotes = {'1️⃣': 0, '2️⃣': 1, '3️⃣': 2}

    @tasks.loop(seconds=1)
    async def run_schedule(self):
        self.run_schedule.change_interval(seconds=self.get_interval())
        if self.first:
            self.first = False
            return
        members = random.sample(self.server().members, k=3)
        self.impostor, self.crewmate1, self.crewmate2 = members
        self.order = [self.impostor, self.crewmate1, self.crewmate2]
        random.shuffle(self.order)
        self.message = await self.chat().send(self.text['start'] % (self.values['reward'], self.values['crewmate'], self.values['crewmate'], self.values['limit'], self.order[0].display_name, self.order[1].display_name, self.order[2].display_name))
        await self.message.add_reaction('1️⃣')
        await self.message.add_reaction('2️⃣')
        await self.message.add_reaction('3️⃣')

    async def on_reaction_add(self, reaction: Reaction, member: Member) -> None:
        if self.message is None or self.message.id != reaction.message.id or reaction.emoji not in ['1️⃣', '2️⃣', '3️⃣']:
            return
        if self.reactions.get(member.id):
            await reaction.message.remove_reaction(reaction, member)
        elif reaction.emoji in self.emotes:
            index = self.emotes[reaction.emoji]
            self.votes[index] += 1
            self.reactions[member.id] = index
        if len(self.reactions) == self.values['limit']:
            index = self.votes.index(max(self.votes))
            username = self.text['none'] if self.votes.count(max(self.votes)) > 1 else self.order[index].display_name
            impostor = self.order.index(self.impostor) if self.impostor in self.order else -1
            users = []
            usernames = ''
            for key in self.reactions:
                if self.reactions[key] == impostor:
                    users.append(key)
                    usernames += ', ' + self.member(key).display_name
            usernames = self.text['none'] if usernames == '' else usernames[2:]
            await reaction.message.channel.send(self.text['end'] % (username, self.impostor.display_name, usernames))
            for member in users:
                amount = self.database.execute('SELECT amount FROM levels WHERE id = %s;', member)
                if len(amount) == 0:
                    self.database.execute('INSERT INTO levels (id, amount) VALUES(%s, 1);', member)
                else:
                    self.database.execute('UPDATE levels SET amount = %s WHERE id = %s;', amount[0][0] + self.values['reward'], member)
            self.message = None
            self.reactions = {}
            self.order = []
            self.impostor = None
            self.crewmate1 = None
            self.crewmate2 = None
            self.votes = [0, 0, 0]

    async def on_reaction_remove(self, reaction: Reaction, member: Member) -> None:
        if self.message is None or self.message.id != reaction.message.id or reaction.emoji not in ['1️⃣', '2️⃣', '3️⃣']:
            return
        index = self.emotes.get(reaction.emoji)
        if index is not None:
            self.votes[index] -= 1
            if self.reactions.get(member.id) == index:
                self.reactions.pop(member.id)

    def get_interval(self) -> int:
        return self.config.intervals['among_us'] + 2 * random.randint(0, self.config.intervals['among_us_offset']) - self.config.intervals['among_us_offset']


class CapsModeration(Module):
    async def on_message(self, message: Message) -> None:
        if self.is_team(message.author):
            return
        content = message.content
        if len(content) < self.values['min']:
            return
        if sum(1 for elem in content if elem.isupper()) / len(content) > self.values['ratio']:
            await self.error_and_delete(message, self.text % message.author.mention)


class Clear(Module):
    async def on_message(self, message: Message) -> None:
        content = message.content.lower()
        if content.startswith('!clear '):
            if self.is_team(message.author):
                strings = content.split()
                if len(strings) > 1 and strings[1].isnumeric():
                    async for m in message.channel.history(limit=int(strings[1])):
                        await m.delete()
            else:
                await self.error_and_delete(message, self.config.texts['team_only'])


class Counter(Module):
    async def on_message(self, message: Message) -> None:
        if ' ' in message.content:
            return
        content = message.content.lower()
        variable = None
        amount = 0
        update = True
        if content.endswith('='):
            variable = content.replace('=', '')
            update = False
        elif content.endswith('++') and content.count('++') == 1:
            variable = content.replace('++', '')
            amount = 1
        elif content.endswith('--') and content.count('--') == 1:
            variable = content.replace('--', '')
            amount = -1
        elif content.find('+=') and content.count('+=') == 1:
            strings = content.split('+=')
            if len(strings) == 2 and strings[1].isnumeric():
                variable = strings[0]
                amount = int(strings[1])
        elif content.find('-=') and content.count('-=') == 1:
            strings = content.split('-=')
            if len(strings) == 2 and strings[1].isnumeric():
                variable = strings[0]
                amount = -int(strings[1])
        if variable is not None:
            if amount != 0 and update:
                old = self.database.execute('SELECT value FROM counter WHERE id = %s;', variable)
                if not old:
                    self.database.execute('INSERT INTO counter (id, value) VALUES(%s, %s);', variable, amount)
                else:
                    amount += old[0][0]
                    self.database.execute('UPDATE counter SET value = %s WHERE id = %s;', amount, variable)
            await message.channel.send(f'{variable} = {self.database.execute("SELECT value FROM counter WHERE id = %s;", variable)[0][0]}')


class DefaultRole(Module):
    async def on_member_join(self, member: Member) -> None:
        await member.add_roles(self.default_role())

    async def on_ready(self) -> None:
        await super().on_ready()
        for i in [i for i in self.server().members if not i.get_role(self.default_role().id)]:
            await i.add_roles(self.default_role())


class Creeper(Module):
    async def on_message(self, message: Message) -> None:
        content = message.content.lower()
        if any(keyword in content for keyword in ('!creeper', 'creeper', 'creper')):
            await message.channel.send(self.text)


class EmbedOnlyChannel(Module):
    async def on_message(self, message: Message) -> None:
        if message.channel.id not in self.config.channels['embed_only']:
            return
        if self.is_team(message.author):
            return
        images = [e for e in message.attachments if e.content_type != 'image' and e.content_type != 'video']
        if len(images) == 0:
            await self.error_and_delete(message, self.text % message.author.mention)


class EmoteModeration(Module):
    async def on_message(self, message: Message) -> None:
        if self.is_team(message.author):
            return
        content = message.content
        emotes = content.count('<a:') + (demoji.demojize(content).count(':') - content.count(':')) // 2
        if emotes > self.values:
            await self.error_and_delete(message, self.text % message.author.mention)


class Flomote(Module):
    async def on_message(self, message: Message) -> None:
        content = message.content.lower()
        if content.startswith('flomote'):
            await message.channel.send(self.text['flomote'])
        if content.startswith('floeyes'):
            await message.channel.send(self.text['floeyes'])


class Help(Module):
    async def on_message(self, message: Message) -> None:
        if message.content.lower().startswith('!help'):
            if message.channel.id != self.bots().id:
                await self.error_and_delete(message, self.config.texts['wrong_channel'] % ('!help', self.bots().mention))
                return
            args = message.content.split()
            if len(args) == 1:
                await self.error_and_delete(message, self.text['missing'])
                return
            try:
                await message.channel.send(self.text['command'][args[1]])
            except KeyError:
                await self.error_and_delete(message, self.text['invalid'] % args[1])


class Levels(Module):
    def __init__(self, config: Config, name: str):
        super().__init__(config, name)
        self.cooldowns = []
        self.levels = {}
        self.roles = {}

    def load(self) -> None:
        super().load()
        base = self.values['base']
        multiplier = self.values['multiplier']
        self.levels = {0: 0, 1: base}
        for i in range(2, self.values['max']):
            self.levels[i] = int(self.levels[i - 1] + base * multiplier ** i)
        roles = self.config.roles['level']
        self.roles = {int(i): roles[i] for i in roles if i.isdigit()}

    @tasks.loop(minutes=1)
    async def run_schedule(self) -> None:
        self.cooldowns = []
        for vc in self.server().voice_channels:
            if len(vc.members) > 1 and vc.category_id != self.tickets_category().id:
                for member in vc.members:
                    if not member.voice.afk and ((not member.voice.mute and not member.voice.self_mute) or member.voice.self_stream):
                        self.award_level(member)

    async def on_message(self, message: Message) -> None:
        content = message.content
        if content.startswith(('!leaderboard', '!lb')):
            args = content.split()
            lb = {}
            start = 0
            if len(args) == 1:
                lb = self.get_lb(min(self.values['leaderboard_default'], len(self.server().members) - 1))
            elif args[1].isdigit():
                lb = self.get_lb(min(int(args[1]), self.values['leaderboard_max'], len(self.server().members) - 1))
            elif '-' in args[1]:
                ints = args[1].split('-')
                if len(ints) == 2 and (i.isdigit for i in ints):
                    try:
                        start = max(1, int(ints[0]))
                        end = min(int(ints[1]), start + self.values['leaderboard_max'], len(self.server().members) - 1)
                        if start >= end:
                            await self.error_and_delete(message, self.text['invalid'])
                            return
                        lb = self.get_lb(end, start - 1)
                    except ValueError:
                        await self.error_and_delete(message, self.text['invalid'])
                        return
                else:
                    await self.error_and_delete(message, self.text['invalid'])
                    return
            text = ''
            for rank, key in enumerate(lb, start=1):
                text += self.text['row'] % (rank if start == 0 else rank + start - 1, self.member(key).mention, lb[key], await self.get_level(lb[key]))
            await message.channel.send(text)
        elif content.startswith(('!level', '!rank')):
            if message.channel.id == self.bots().id:
                args = content.split()
                if len(message.mentions) > 1 or len(args) > 2:
                    await self.error_and_delete(message, self.text['multiple_arguments'])
                    return
                else:
                    member = message.author if len(args) == 1 else await self.member_from_id(args[1], message)
                    if member.id is None:
                        return
                amount = self.get_from_database(member.id)
                if not amount:
                    await message.channel.send(self.text['no_xp'] % member.mention)
                    return
                amount = amount[0][0]
                level = await self.get_level(amount)
                to_next = self.levels[level + 1] - amount
                rank = self.get_rank(member.id)
                if rank[1] is None:
                    await message.channel.send(self.text['success_1'] % (member.mention, level, amount, rank[0], member.mention, to_next))
                else:
                    await message.channel.send(self.text['success'] % (member.mention, level, amount, rank[0], member.mention, to_next, member.mention, rank[1]))
                for key in self.roles:
                    if level >= key:
                        await self.member(member.id).add_roles(self.role(self.roles[key]))
            else:
                await self.error_and_delete(message, self.config.texts['wrong_channel'] % ('!level', self.bots().mention))
            return
        if message.channel.id in self.config.channels['level']:
            self.award_level(message.author)

    async def on_ready(self) -> None:
        await super().on_ready()
        for i in [i for i in self.server().members if i.get_role(self.special_requirement_role().id)]:
            await i.remove_roles(self.special_role())
        special = random.choice([i for i in self.server().members if not self.is_team(i) and i.get_role(self.special_requirement_role().id)])
        await special.add_roles(self.special_role())
        await self.chat().send(self.text['special_notification'] % special.mention, allowed_mentions=AllowedMentions.all())

    async def get_level(self, xp: int) -> int:
        for key in self.levels:
            value = self.levels[key]
            if xp < value:
                return key - 1
        return self.values['max']

    def get_lb(self, end: int, begin: int = 0) -> dict:
        lb = dict(self.database.execute('SELECT * FROM levels;'))
        result = {}
        for k in lb.keys():
            # noinspection PyTypeChecker
            if self.member(k) is not None:
                result[k] = lb[k]
        return dict(sorted(result.items(), key=lambda x: x[1], reverse=True)[begin:end])

    def get_rank(self, member: int) -> tuple:
        value = self.get_from_database(member)
        if not value:
            return 0, None
        value = value[0][0]
        values = list(self.get_lb(len(self.server().members)).items())
        if values[0][1] == value:
            return 1, None
        for i in range(1, len(values)):
            if values[i][1] == value:
                return i + 1, values[i - 1][1] - value
        return len(values), values[len(values) - 1][1] - value

    def get_from_database(self, member: int) -> list[tuple]:
        return self.database.execute('SELECT amount FROM levels WHERE id = %s;', member)

    def award_level(self, member: Member) -> None:
        if member not in self.cooldowns:
            self.cooldowns.append(member)
            amount = self.get_from_database(member.id)
            multiplier = 1
            if member.get_role(self.premium_role().id):
                multiplier *= self.values['premium']
            if member.get_role(self.special_role().id):
                multiplier *= self.values['special']
            if amount is None or len(amount) == 0:
                self.database.execute('INSERT INTO levels (id, amount) VALUES(%s, 1);', member.id)
            else:
                self.database.execute('UPDATE levels SET amount = %s WHERE id = %s;', amount[0][0] + int(random.randrange(self.values['give_min'], self.values['give_max'] + 1) * multiplier), member.id)


class Logger(Module):
    async def on_member_join(self, member: Member) -> None:
        embed = self.embed(self.text['guild_joined'])
        embed.add_field(name=self.text['user'], value=str(member), inline=False)
        embed.add_field(name=self.text['ping'], value=member.mention, inline=False)
        embed.add_field(name=self.text['created'], value=self.readable_datetime(str(member.created_at)), inline=True)
        embed.set_thumbnail(url=member.display_avatar.url)
        await self.join_log().send(embed=embed)

    async def on_member_remove(self, member: Member) -> None:
        embed = self.error_embed(title=self.text['guild_left'])
        embed.add_field(name=self.text['user'], value=str(member), inline=False)
        embed.add_field(name=self.text['ping'], value=member.mention, inline=False)
        embed.add_field(name=self.text['created'], value=self.readable_datetime(str(member.created_at)), inline=False)
        embed.add_field(name=self.text['joined'], value=self.readable_datetime(str(member.joined_at)), inline=True)
        embed.set_thumbnail(url=member.display_avatar.url)
        await self.leave_log().send(embed=embed)

    async def on_member_update(self, before: Member, after: Member) -> None:
        if after.nick != before.nick:
            embed = self.embed(self.text['nick_updated'])
            embed.add_field(name=self.text['user'], value=str(before), inline=False)
            embed.add_field(name=self.text['ping'], value=before.mention, inline=False)
            embed.add_field(name=self.text['before'], value=before.nick, inline=False)
            embed.add_field(name=self.text['after'], value=after.nick, inline=True)
            await self.member_log().send(embed=embed)
        if after.guild_avatar is not None and before.guild_avatar is None:
            embed = self.embed(self.text['guild_avatar_added'])
            embed.add_field(name=self.text['user'], value=str(before), inline=False)
            embed.add_field(name=self.text['ping'], value=before.mention, inline=True)
            embed.set_image(url=after.guild_avatar.url)
            await self.member_log().send(embed=embed)
        if after.guild_avatar is None and before.guild_avatar is not None:
            embed = self.embed(self.text['guild_avatar_updated'])
            embed.add_field(name=self.text['user'], value=str(before), inline=False)
            embed.add_field(name=self.text['ping'], value=before.mention, inline=True)
            embed.set_thumbnail(url=before.guild_avatar.url)
            await self.member_log().send(embed=embed)
        if after.guild_avatar != before.guild_avatar:
            embed = self.embed(self.text['guild_avatar_updated'])
            embed.add_field(name=self.text['user'], value=str(before), inline=False)
            embed.add_field(name=self.text['ping'], value=before.mention, inline=True)
            embed.set_thumbnail(url=before.guild_avatar.url)
            embed.set_image(url=after.guild_avatar.url)
            await self.member_log().send(embed=embed)

    async def on_user_update(self, before: User, after: User) -> None:
        if str(after) != str(before):
            embed = self.embed(self.text['name_updated'])
            embed.add_field(name=self.text['ping'], value=before.mention, inline=False)
            embed.add_field(name=self.text['before'], value=str(before), inline=False)
            embed.add_field(name=self.text['after'], value=str(after), inline=True)
            await self.member_log().send(embed=embed)
        if after.global_name != before.global_name:
            embed = self.embed(self.text['global_name_updated'])
            embed.add_field(name=self.text['user'], value=str(before), inline=False)
            embed.add_field(name=self.text['ping'], value=before.mention, inline=False)
            embed.add_field(name=self.text['before'], value=before.global_name, inline=False)
            embed.add_field(name=self.text['after'], value=after.global_name, inline=True)
            await self.member_log().send(embed=embed)
        if after.avatar.url != before.avatar.url:
            embed = self.embed(self.text['avatar_updated'])
            embed.add_field(name=self.text['user'], value=str(before), inline=False)
            embed.add_field(name=self.text['ping'], value=before.mention, inline=True)
            embed.set_thumbnail(url=before.avatar.url)
            embed.set_image(url=after.avatar.url)
            await self.member_log().send(embed=embed)

    async def on_message_edit(self, before: Message, after: Message) -> None:
        old = before.content
        new = after.content
        if old != new:
            embed = self.embed(self.text['message_edited'])
            embed.add_field(name=self.text['user'], value=before.author.mention, inline=False)
            embed.add_field(name=self.text['channel'], value=before.channel.mention, inline=False)
            embed.add_field(name=self.text['before'], value=old, inline=False)
            embed.add_field(name=self.text['after'], value=new, inline=True)
            await self.message_log().send(embed=embed)

    async def on_message_delete(self, message: Message) -> None:
        embed = self.error_embed(self.text['message_deleted'])
        embed.add_field(name=self.text['user'], value=message.author.mention, inline=False)
        embed.add_field(name=self.text['channel'], value=message.channel.mention, inline=False)
        embed.add_field(name=self.text['message'], value=message.content, inline=True)
        await self.message_log().send(embed=embed)

    async def on_voice_state_update(self, member: Member, before: VoiceState, after: VoiceState) -> None:
        if before.channel is not None and after.channel is not None:
            embed = self.embed(self.text['voice_switched'])
            embed.add_field(name=self.text['user'], value=member.mention, inline=False)
            embed.add_field(name=self.text['before'], value=before.channel.name, inline=False)
            embed.add_field(name=self.text['after'], value=after.channel.name, inline=True)
            await self.voice_log().send(embed=embed)
        elif before.channel is None and after.channel is not None:
            embed = self.embed(self.text['voice_joined'])
            embed.add_field(name=self.text['user'], value=member.mention, inline=False)
            embed.add_field(name=self.text['channel'], value=after.channel.name, inline=True)
            await self.voice_log().send(embed=embed)
        elif before.channel is not None and after.channel is None:
            embed = self.error_embed(self.text['voice_left'])
            embed.add_field(name=self.text['user'], value=member.mention, inline=False)
            embed.add_field(name=self.text['channel'], value=before.channel.name, inline=True)
            await self.voice_log().send(embed=embed)


# noinspection PyTypeChecker
class Moderation(Module):
    async def warn(self, member: Member, reason: str, team_member: User, channel: TextChannel):
        now = datetime.now()
        self.database.execute('INSERT INTO warns (member, reason, time, team_member) VALUES(%s, %s, %s, %s);', member.id, reason, now, team_member.id)
        await channel.send(self.text['warn_success'] % (member.mention, reason, team_member.mention))
        await self.moderation_log().send(self.text['warn_success'] % (member.mention, reason, team_member.mention))
        databasecontents = self.database.execute('SELECT * FROM warns WHERE member = %s ORDER BY id;', member.id)
        active = 0
        for i in databasecontents:
            if (now - datetime.strptime(i[3][:19], '%Y-%m-%d %H:%M:%S')).days < self.values['warn_expire_days']:
                active += 1
        if active >= self.values['mute_warnings']:
            await self.timeout(member, self.values['mute_duration'], self.text['too_many_warnings'], self.bot_user(), channel)
        if active >= self.values['kick_warnings']:
            await self.kick(member, self.text['too_many_warnings'], self.bot_user(), channel)
        if active >= self.values['ban_warnings']:
            await self.ban(member, self.text['too_many_warnings'], self.bot_user(), channel)

    async def timeout(self, member: Member, duration: int, reason: str, team_member: User, channel: TextChannel) -> None:
        await member.timeout(datetime.now().astimezone() + timedelta(seconds=duration), reason=reason)
        await channel.send(self.text['mute_success'] % (member.mention, reason, team_member.mention))
        await self.moderation_log().send(self.text['mute_success'] % (member.mention, reason, team_member.mention))
        await member.add_roles(self.muted_role())

    async def kick(self, member: Member, reason: str, team_member: User, channel: TextChannel) -> None:
        await member.kick(reason=reason)
        await channel.send(self.text['kick_success'] % (member.mention, reason, team_member.mention))
        await self.moderation_log().send(self.text['kick_success'] % (member.mention, reason, team_member.mention))

    async def ban(self, member: Member, reason: str, team_member: User, channel: TextChannel) -> None:
        await member.ban(reason=reason, delete_message_days=1)
        await channel.send(self.text['ban_success'] % (member.mention, reason, team_member.mention))
        await self.moderation_log().send(self.text['ban_success'] % (member.mention, reason, team_member.mention))

    async def on_message(self, message: Message) -> None:
        args = message.content.split()
        args[0] = args[0].lower()
        if args[0] == '!warn':
            if not self.is_team(message.author):
                await self.error_and_delete(message, self.config.texts['team_only'])
                return
            if len(args) < 3:
                await self.error_and_delete(message, self.text['warn_failure'])
                return
            member = await self.non_team_member_from_id(args[1], message)
            if member is None:
                return
            await self.warn(member, ' '.join(args[2:]), message.author, message.channel)
        elif args[0] == '!removewarn':
            if not self.is_team(message.author):
                await self.error_and_delete(message, self.config.texts['team_only'])
                return
            if len(args) < 2:
                await self.error_and_delete(message, self.text['removewarn_failure'])
                return
            try:
                warn = int(args[1])
            except ValueError:
                await self.error_and_delete(message, self.text['removewarn_failure'])
                return
            self.database.execute('DELETE FROM warns WHERE id = %s;', warn)
            await message.channel.send(self.text['removewarn_success'] % warn)
            await self.moderation_log().send(self.text['removewarn_success'] % warn)
        elif args[0] == '!warnings':
            if message.channel.id != self.bots().id:
                await self.error_and_delete(message, self.config.texts['wrong_channel'] % ('!warnings', self.bots().mention))
                return
            if len(message.mentions) > 1:
                await self.error_and_delete(message, self.text['multiple_arguments'])
                return
            member = message.author if len(args) == 1 else await self.member_from_id(args[1], message)
            if member is None:
                return
            databasecontents = self.database.execute('SELECT * FROM warns WHERE member = %s ORDER BY id;', member.id)
            result = self.text['warnings_success'] % member.mention
            if not databasecontents:
                result += self.text['warnings_none']
            else:
                for i in databasecontents:
                    result += self.text['warnings_item'] % (self.readable_datetime(i[3]), i[2], self.member(i[4]).mention, i[0])
                    if (datetime.now() - datetime.strptime(i[3][:19], '%Y-%m-%d %H:%M:%S')).days >= self.values['warn_expire_days']:
                        result += self.text['warnings_expired']
            await message.channel.send(result)
        elif args[0] == '!mute':
            if not self.is_team(message.author):
                await self.error_and_delete(message, self.config.texts['team_only'])
                return
            if len(args) < 4:
                await self.error_and_delete(message, self.text['mute_failure'])
                return
            member = await self.non_team_member_from_id(args[1], message)
            if member is not None:
                await self.timeout(member, self.get_duration(args[2]), ' '.join(args[3:]), self.bot_user(), message.channel)
        elif args[0] == '!unmute':
            if not self.is_team(message.author):
                await self.error_and_delete(message, self.config.texts['team_only'])
                return
            if len(args) < 2:
                await self.error_and_delete(message, self.text['unmute_failure'])
                return
            member = await self.non_team_member_from_id(args[1], message)
            if member is not None:
                reason = self.text['no_reason'] if len(args) == 2 else ' '.join(args[2:])
                await member.timeout(None, reason=reason)
                await message.channel.send(self.text['unmute_success'] % (member.mention, reason, message.author.mention))
                await self.moderation_log().send(self.text['unmute_success'] % (member.mention, reason, message.author.mention))
        elif args[0] == '!kick':
            if not self.is_team(message.author):
                await self.error_and_delete(message, self.config.texts['team_only'])
                return
            if len(args) < 3:
                await self.error_and_delete(message, self.text['kick_failure'])
                return
            member = await self.non_team_member_from_id(args[1], message)
            if member is not None:
                await self.kick(member, ' '.join(args[2:]), self.bot_user(), message.channel)
        elif args[0] == '!ban':
            if not self.is_team(message.author):
                await self.error_and_delete(message, self.config.texts['team_only'])
                return
            if len(args) < 3:
                await self.error_and_delete(message, self.text['ban_failure'])
                return
            member = await self.non_team_member_from_id(args[1], message)
            if member is not None:
                await self.ban(member, ' '.join(args[2:]), self.bot_user(), message.channel)
        else:
            if self.vip_role() in message.author.roles or self.builder_role() in message.author.roles or self.is_team(message.author):
                return
            blacklist = set(self.values['ping_blacklist'])
            for member in message.mentions:
                if member.id in blacklist:
                    await self.warn(message.author, self.text['ping_reason'], self.bot_user(), message.channel)
                    await message.delete()


class Ping(Module):
    async def on_message(self, message: Message) -> None:
        if message.content.lower().startswith('!ping'):
            created_at = message.created_at
            now = datetime.now(timezone.utc)
            time = str(now - created_at) if now > created_at else str(created_at - now)
            if time.startswith('0:00:'):
                time = time[5:]
            if time.startswith('00'):
                time = time[1:]
            await message.channel.send(self.text % time)


class PrankMute(Module):
    async def on_message(self, message: Message) -> None:
        args = message.content.split()
        if args[0].lower() == '?mute':
            if not message.author.get_role(self.prank_mute_requirement_role().id):
                await self.error_and_delete(message, self.text['failure'])
                return
            if len(args) == 1:
                await self.error_and_delete(message, self.text['missing_user'])
                return
            if len(args) == 2:
                await self.error_and_delete(message, self.text['missing_reason'])
                return
            member = await self.member_from_id(args[1], message)
            if member is None:
                return
            reason = ' '.join(args[2:])
            await member.timeout(datetime.now().astimezone() + timedelta(seconds=86400), reason=reason)
            await message.channel.send(self.text['start'] % (member.mention, reason, message.author.mention), delete_after=self.config.values['delete_after'])
            await asyncio.sleep(self.values)
            await member.timeout(None)
            await message.channel.send(self.text['end'])


class RawEcho(Module):
    async def on_message(self, message: Message) -> None:
        content = message.content.lower()
        if content.startswith('!rawecho '):
            await message.channel.send(f'`{content[len("!rawecho "):]}`')


class Reload(Module):
    async def on_message(self, message: Message) -> None:
        if message.content.lower().startswith('!reload') and self.is_team(message.author):
            await message.channel.send(self.text['start'])
            self.config.load()
            await message.channel.send(self.text['end'])


class RockPaperScissors(Module):
    def __init__(self, config: Config, name: str):
        super().__init__(config, name)
        self.players = []

    async def on_message(self, message: Message) -> None:
        content = message.content.lower()
        if content.startswith('!ssp') and message.author.id not in self.players:
            self.players.append(message.author.id)
            await message.channel.send(self.text['start'])
        elif message.author.id in self.players:
            self.players.remove(message.author.id)
            if content.startswith(self.text['rock'].lower()):
                result = self.get_result(0)
            elif content.startswith(self.text['paper'].lower()):
                result = self.get_result(1)
            elif content.startswith(self.text['scissors'].lower()):
                result = self.get_result(2)
            else:
                result = self.text['invalid']
            await message.channel.send(result)

    def get_result(self, prompt: int) -> str:
        choice = random.choice([0, 1, 2])
        texts = [self.text['rock'], self.text['paper'], self.text['scissors']]
        if (prompt == 0 and choice == 1) or (prompt == 1 and choice == 2) or (prompt == 2 and choice == 0):
            return self.text['result'] % (texts[prompt], texts[choice], self.text['lose'])
        elif (prompt == 1 and choice == 0) or (prompt == 2 and choice == 1) or (prompt == 0 and choice == 2):
            return self.text['result'] % (texts[prompt], texts[choice], self.text['win'])
        else:
            return self.text['result'] % (texts[prompt], texts[choice], self.text['draw'])


class Roles(Module):
    async def on_message(self, message: Message) -> None:
        content = message.content.lower()
        if self.is_team(message.author):
            if content.startswith('!chatsupport'):
                await message.author.add_roles(self.chat_support_role())
                await message.channel.send(self.text['chatsupport'])
            elif content.startswith('!keinchatsupport'):
                await message.author.remove_roles(self.chat_support_role())
                await message.channel.send(self.text['keinchatsupport'])
            elif content.startswith('!voicesupport'):
                await message.author.add_roles(self.voice_support_role())
                await message.channel.send(self.text['voicesupport'])
            elif content.startswith('!keinvoicesupport'):
                await message.author.remove_roles(self.voice_support_role())
                await message.channel.send(self.text['keinvoicesupport'])


class Rules(Module):
    def __init__(self, config: Config, name: str):
        super().__init__(config, name)
        self.messages = 0

    @tasks.loop(seconds=1)
    async def run_schedule(self):
        if self.messages > int(self.values):
            await self.chat().send(self.text % (self.rules().mention, self.short_rules().mention))
            self.messages = 0

    async def on_message(self, message: Message) -> None:
        if message.channel.id == self.chat().id:
            self.messages += 1
        if message.content.lower().startswith('!regeln'):
            await message.channel.send(self.text % (self.rules().mention, self.short_rules().mention))
            self.messages = 0


class SelfDestruct(Module):
    async def on_message(self, message: Message) -> None:
        if message.content.lower().startswith('!selbstzerstörung'):
            msg = await message.channel.send(embed=self.make_embed('text_3'))
            await asyncio.sleep(1)
            await msg.edit(embed=self.make_embed('text_2'))
            await asyncio.sleep(1)
            await msg.edit(embed=self.make_embed('text_1'))
            await asyncio.sleep(1)
            await msg.edit(embed=self.make_embed('text_0'))
            await message.channel.send(self.text['image_0'])

    def make_embed(self, text_id: str) -> Embed:
        embed = self.embed(self.text['title'])
        embed.set_thumbnail(url=self.text['image_1'])
        embed.add_field(name=self.text[text_id], value='', inline=True)
        return embed


class Slowmode(Module):
    def __init__(self, config: Config, name: str):
        super().__init__(config, name)
        self.messages = 0

    @tasks.loop(seconds=1)
    async def run_schedule(self):
        if self.messages > 15:
            await self.chat().edit(slowmode_delay=15)
        elif self.messages > 10:
            await self.chat().edit(slowmode_delay=10)
        elif self.messages > 5:
            await self.chat().edit(slowmode_delay=5)
        else:
            await self.chat().edit(slowmode_delay=0)
        self.messages = 0

    async def on_message(self, message: Message) -> None:
        if message.channel.id == self.chat().id:
            self.messages += 1


class TempVoice(Module):
    def __init__(self, config: Config, name: str):
        super().__init__(config, name)
        self.channels = {}
        self.connect = {}
        self.view = {}

    @tasks.loop(seconds=1)
    async def run_schedule(self):
        for vc in self.server().voice_channels:
            if vc.category_id == self.voice_category().id and vc.id != self.afk().id and vc.id != self.voice_join().id and vc.id != self.voice_move().id and not vc.members:
                self.channels = {k: v for k, v in self.channels.items() if v != vc.id}
                self.connect = {k: v for k, v in self.connect.items() if k != vc.id}
                self.view = {k: v for k, v in self.view.items() if k != vc.id}
                await vc.delete()

    async def on_message(self, message: Message) -> None:
        content = message.content
        if content.lower().startswith('!vc '):
            if message.channel.id != self.bots().id:
                await self.error_and_delete(message, self.config.texts['wrong_channel'] % ('!vc', self.bots().mention))
                return
            author = message.author.id
            if self.is_team(message.author):
                channel = [vc for vc in [self.voice_channel(vc) for vc in self.channels.values()] if message.author in vc.members][0]
                if channel is None:
                    await self.error_and_delete(message, self.text['team_failure'])
                    return
                channel_id = channel.id
            else:
                if author not in self.channels:
                    await self.error_and_delete(message, self.text['failure'])
                    return
                channel_id = self.channels[author]
                channel = self.voice_channel(channel_id)
            args = content.split()
            args[1] = args[1].lower()
            if args[1] == 'show':
                self.view[channel_id] = True
                await self.update_channel(message.author)
                await message.channel.send(self.text['show'])
                await self.voice_log().send(self.text['show_log'] % author)
            elif args[1] == 'hide':
                self.view[channel_id] = False
                await self.update_channel(message.author)
                await message.channel.send(self.text['hide'])
                await self.voice_log().send(self.text['hide_log'] % author)
            elif args[1] == 'open':
                self.connect[channel_id] = True
                await self.update_channel(message.author)
                await message.channel.send(self.text['open'])
                await self.voice_log().send(self.text['open_log'] % author)
            elif args[1] == 'close':
                self.connect[channel_id] = False
                await self.update_channel(message.author)
                await message.channel.send(self.text['close'])
                await self.voice_log().send(self.text['close_log'] % author)
            elif args[1] == 'limit':
                if len(args) == 2:
                    await self.error_and_delete(message, self.text['limit_missing'])
                    return
                try:
                    limit = int(args[2])
                except TypeError:
                    await self.error_and_delete(message, self.text['limit_failure'])
                    return
                if limit < 0 or limit > 99:
                    await self.error_and_delete(message, self.text['limit_failure'])
                    return
                await channel.edit(user_limit=limit)
                await message.channel.send(self.text['limit_success'] % limit)
                await self.voice_log().send(self.text['limit_log'] % (author, limit))
            elif args[1] == 'name':
                if len(args) == 2:
                    await self.error_and_delete(message, self.text['name_failure'])
                    return
                name = ' '.join(args[2:])
                await channel.edit(name=self.text['name'] % name)
                await message.channel.send(self.text['name_success'] % name)
                await self.voice_log().send(self.text['name_log'] % (author, name))
            elif args[1] == 'soundboard':
                soundboard = not channel.permissions_for(self.default_role()).use_soundboard
                await channel.set_permissions(target=self.default_role(), use_soundboard=soundboard)
                await channel.set_permissions(target=self.default_role(), use_external_sounds=soundboard)
                await message.channel.send(self.text['soundboard_on' if soundboard else 'soundboard_off'])
                await self.voice_log().send(self.text['soundboard_log_on' if soundboard else 'soundboard_log_off'] % author)
            else:
                await self.error_and_delete(message, self.text['invalid'] % args[1])

    async def on_voice_state_update(self, member: Member, before: VoiceState, after: VoiceState) -> None:
        if after.channel == self.voice_join():
            if member.id not in self.channels:
                await self.create_channel(member)
            await member.move_to(self.voice_channel(self.channels[member.id]))

    async def create_channel(self, member: Member) -> None:
        try:
            self.channels[member.id] = (await self.server().create_voice_channel(self.text['name'] % member.display_name, category=self.voice_category(), overwrites={
                self.server().default_role: PermissionOverwrite(view_channel=False, connect=False),
                self.default_role(): PermissionOverwrite(view_channel=True, connect=True),
                self.test_moderator(): PermissionOverwrite(view_channel=True, connect=True),
                self.moderator(): PermissionOverwrite(view_channel=True, connect=True),
                member: PermissionOverwrite(move_members=True)
            })).id
            self.connect[self.channels[member.id]] = True
            self.view[self.channels[member.id]] = True
            await asyncio.sleep(1)
        except HTTPException:
            await asyncio.sleep(1)
            await self.create_channel(member)

    async def update_channel(self, owner: Member) -> None:
        channel_id = self.channels[owner.id]
        await self.voice_channel(channel_id).set_permissions(target=self.default_role(), connect=self.connect[channel_id], view_channel=self.view[channel_id])


class Tickets(Module):
    async def on_message(self, message: Message) -> None:
        content = message.content.lower()
        if content.startswith('!ticket'):
            if message.channel.id == self.tickets().id:
                ticket = self.database.execute('SELECT channel FROM tickets WHERE owner = %s', message.author.id)
                if ticket:
                    await self.error_and_delete(message, self.text['ticket_failure'] % self.text_channel(ticket[0][0]))
                    return
                self.database.execute('INSERT INTO tickets (channel, owner) VALUES(%s, %s);', 0, message.author.id)
                ticket = await self.server().create_text_channel(name=self.text['name'] % self.database.execute('SELECT id FROM tickets WHERE owner = %s;', message.author.id), category=self.tickets_category(), overwrites={
                    self.server().default_role: PermissionOverwrite(read_messages=False),
                    self.server().me: PermissionOverwrite(read_messages=True),
                    message.author: PermissionOverwrite(read_messages=True),
                    self.test_moderator(): PermissionOverwrite(read_messages=True),
                    self.moderator(): PermissionOverwrite(read_messages=True),
                })
                self.database.execute('UPDATE tickets SET channel = %s WHERE owner = %s;', ticket.id, message.author.id)
                await ticket.send(self.text['ticket_success'] % (self.chat_support_role().mention, message.author.mention), allowed_mentions=AllowedMentions.all())
                await message.delete()
            else:
                await self.error_and_delete(message, self.config.texts['wrong_channel'] % ('!ticket', self.tickets().mention))
                return
        elif message.channel.id == self.tickets().id:
            await self.error_and_delete(message, self.text['ticket_invalid'])
            return
        if content.startswith('!close'):
            if any(i[0] == message.channel.id for i in self.database.execute('SELECT channel FROM tickets;')):
                ticket = self.database.execute('SELECT owner FROM tickets WHERE channel = %s;', message.channel.id)
                await message.channel.set_permissions(target=self.member(ticket[0][0]), read_messages=False)
                await message.channel.send(self.text['close_success'])
            else:
                await self.error_and_delete(message, self.text['close_wrong_channel'])
                return
        if content.startswith('!delete'):
            if not any(i[0] == message.channel.id for i in self.database.execute('SELECT channel FROM tickets;')):
                await self.error_and_delete(message, self.text['delete_wrong_channel'])
                return
            elif not self.is_team(message.author):
                await self.error_and_delete(message, self.config.texts['team_only'])
                return
            else:
                self.database.execute('DELETE FROM tickets WHERE channel = %s;', message.channel.id)
                await self.text_channel(message.channel.id).delete()


class Tricks(Module):
    def __init__(self, config: Config, name: str):
        super().__init__(config, name)
        self.tricks = {}

    async def on_message(self, message: Message) -> None:
        content = message.content.lower()
        if content.startswith('!'):
            if content.startswith('!addtrick'):
                if not self.is_team(message.author):
                    await self.error_and_delete(message, self.config.texts['team_only'])
                    return
                split = message.content.split()
                if len(split) > 2:
                    name = split[1].lower()
                    text = message.content.replace('!addtrick ' + name + ' ', '')
                    self.database.execute('INSERT INTO tricks (id, text) VALUES(%s, %s);', name, text)
                    self.tricks[name] = text
                    await message.channel.send((self.text['added'] % name) + text)
            elif content.startswith('!removetrick'):
                if not self.is_team(message.author):
                    await self.error_and_delete(message, self.config.texts['team_only'])
                    return
                split = message.content.split()
                if len(split) > 1:
                    name = split[1].lower()
                    self.database.execute('DELETE FROM tricks WHERE id = %s;', name)
                    self.tricks.pop(name)
                    await message.channel.send(self.text['removed'] % name)
            elif content.startswith('!tricks'):
                if message.channel.id != self.bots().id:
                    await self.error_and_delete(message, self.config.texts['wrong_channel'] % ('!tricks', self.bots().mention))
                    return
                tricklist = '\n'.join(['!' + elem for elem in self.tricks.keys()])
                if tricklist:
                    await message.channel.send(self.text['list'] + self.text['none'])
                else:
                    await message.channel.send(self.text['list'] + tricklist)
            else:
                name = content.split()[0][1:]
                if name in self.tricks:
                    await message.channel.send('**!' + name + '**\n\n' + self.tricks[name])

    async def on_ready(self) -> None:
        await super().on_ready()
        for elem in self.database.execute('SELECT id, text FROM tricks;'):
            self.tricks[elem[0]] = elem[1]


class Userinfo(Module):
    async def on_message(self, message: Message) -> None:
        content = message.content.lower()
        if content.startswith('!userinfo'):
            if message.channel.id != self.bots().id:
                await self.error_and_delete(message, self.config.texts['wrong_channel'] % ('!userinfo', self.bots().mention))
                return
            args = content.split()
            if len(message.mentions) > 1 or len(args) > 2:
                await self.error_and_delete(message, self.text['multiple_arguments'])
                return
            member = message.author if len(args) == 1 else await self.member_from_id(args[1], message)
            if member is None:
                return
            embed = self.embed(member.display_name).set_thumbnail(url=member.avatar)
            embed.add_field(name=self.text['member'], value=member.name + '#' + member.discriminator, inline=False)
            embed.add_field(name=self.text['id'], value=member.id, inline=False)
            embed.add_field(name=self.text['mention'], value=member.mention, inline=False)
            embed.add_field(name=self.text['account_created'], value=self.readable_datetime(str(member.created_at)), inline=False)
            embed.add_field(name=self.text['guild_joined'], value=self.readable_datetime(str(member.joined_at)), inline=False)
            premium = member.premium_since
            if premium is not None:
                embed.add_field(name=self.text['booster_since'], value=self.readable_datetime(str(premium)), inline=False)
            await message.channel.send(embed=embed)


class VoiceSupport(Module):
    async def on_voice_state_update(self, member: Member, before: VoiceState, after: VoiceState) -> None:
        if after.channel is not None and after.channel.id == self.voice_support().id:
            await self.team_voice_support().send(self.text % (self.voice_support_role().mention, member.mention), allowed_mentions=AllowedMentions.all())


class Write(Module):
    async def on_message(self, message: Message) -> None:
        if message.content.startswith('!write ') and self.is_team(message.author):
            args = message.content.split()
            if args[1].startswith('<#') and args[1].endswith('>'):
                args[1] = args[1][2:-1]
            try:
                await self.text_channel(int(args[1])).send(' '.join(args[2:]))
            except ValueError:
                await self.error_and_delete(message, self.config.texts['invalid_channel'])
