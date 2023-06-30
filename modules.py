import asyncio
import random
from datetime import datetime, timedelta, timezone

import discord
import emoji
from discord.ext import tasks

from config import Config
from module import Module


class AmongUs(Module):
    def __init__(self, config: Config):
        super().__init__(config, 1)
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
        self.run_schedule.change_interval(seconds=self.config.intervals['among_us'] + 2 * (random.randint(0, self.config.intervals['among_us']) - self.config.intervals['among_us_offset']))
        if self.first:
            self.first = False
            return
        members = random.sample(self.config.server().members, k=3)
        self.impostor, self.crewmate1, self.crewmate2 = members
        self.order = [self.impostor, self.crewmate1, self.crewmate2]
        random.shuffle(self.order)
        self.message = await self.config.chat().send(self.config.texts['among_us']['start'] % (self.config.values['among_us_reward'], self.config.values['among_us_crewmate'], self.config.values['among_us_crewmate'], self.config.values['among_us_limit'], self.order[0].display_name, self.order[1].display_name, self.order[2].display_name))
        await self.message.add_reaction('1️⃣')
        await self.message.add_reaction('2️⃣')
        await self.message.add_reaction('3️⃣')

    async def on_reaction_add(self, reaction: discord.Reaction, member: discord.Member) -> None:
        if self.message is None or self.message.id != reaction.message.id or reaction.emoji not in ['1️⃣', '2️⃣', '3️⃣']:
            return
        if self.reactions.get(member.id):
            await reaction.message.remove_reaction(reaction, member)
        elif reaction.emoji in self.emotes:
            index = self.emotes[reaction.emoji]
            self.votes[index] += 1
            self.reactions[member.id] = index
        if len(self.reactions) == self.config.values['among_us_limit']:
            index = self.votes.index(max(self.votes))
            username = self.config.texts['among_us']['none'] if self.votes.count(max(self.votes)) > 1 else self.order[index].display_name
            impostor = self.order.index(self.impostor) if self.impostor in self.order else -1
            users = []
            usernames = ''
            for key in self.reactions:
                if self.reactions[key] == impostor:
                    users.append(key)
                    usernames += ', ' + self.config.member(key).display_name
            usernames = self.config.texts['among_us']['none'] if usernames == '' else usernames[2:]
            await reaction.message.channel.send(self.config.texts['among_us']['end'] % (username, self.impostor.display_name, usernames))
            for member in users:
                amount = self.config.database.execute('SELECT amount FROM levels WHERE id = %s;', member)
                if len(amount) == 0:
                    self.config.database.execute('INSERT INTO levels (id, amount) VALUES(%s, 1);', member)
                else:
                    self.config.database.execute('UPDATE levels SET amount = %s WHERE id = %s;', amount[0][0] + self.config.values["among_us_reward"], member)
            self.message = None
            self.reactions = {}
            self.order = []
            self.impostor = None
            self.crewmate1 = None
            self.crewmate2 = None
            self.votes = [0, 0, 0]

    async def on_reaction_remove(self, reaction: discord.Reaction, member: discord.Member) -> None:
        if self.message is None or self.message.id != reaction.message.id or reaction.emoji not in ['1️⃣', '2️⃣', '3️⃣']:
            return
        index = self.emotes.get(reaction.emoji)
        if index is not None:
            self.votes[index] -= 1
            if self.reactions.get(member.id) == index:
                self.reactions.pop(member.id)

    def update_interval(self) -> None:
        self.run_schedule.change_interval(seconds=self.config.intervals['among_us'] + 2 * random.randint(0, self.config.intervals['among_us_offset']) - self.config.intervals['among_us_offset'])


class CapsModeration(Module):
    async def on_message(self, message: discord.Message) -> None:
        if self.config.is_team(message.author):
            return
        content = message.content
        if len(content) < self.config.values['caps_min']:
            return
        if sum(1 for elem in content if elem.isupper()) / len(content) > self.config.values['caps_ratio']:
            await self.error_and_delete(message, self.config.texts['caps_moderation'] % message.author.mention)


class Clear(Module):
    async def on_message(self, message: discord.Message) -> None:
        content = message.content.lower()
        if content.startswith('!clear '):
            if self.config.is_team(message.author):
                strings = content.split()
                if len(strings) > 1 and strings[1].isnumeric():
                    async for m in message.channel.history(limit=int(strings[1])):
                        await m.delete()
            else:
                await self.error_and_delete(message, self.config.texts['team_only'])


class Counter(Module):
    async def on_message(self, message: discord.Message) -> None:
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
                old = self.config.database.execute('SELECT value FROM counter WHERE id = %s;', variable)
                if not old:
                    self.config.database.execute('INSERT INTO counter (id, value) VALUES(%s, %s);', variable, amount)
                else:
                    amount += old[0][0]
                    self.config.database.execute('UPDATE counter SET value = %s WHERE id = %s;', amount, variable)
            await message.channel.send(f'{variable} = {self.config.database.execute("SELECT value FROM counter WHERE id = %s;", variable)[0][0]}')


class Creeper(Module):
    async def on_message(self, message: discord.Message) -> None:
        content = message.content.lower()
        if any(keyword in content for keyword in ('!creeper', 'creeper', 'creper')):
            await message.channel.send(self.config.texts['creeper'])


class EmoteModeration(Module):
    async def on_message(self, message: discord.Message) -> None:
        if self.config.is_team(message.author):
            return
        content = message.content
        emotes = content.count('<a:') + (emoji.demojize(content).count(':') - content.count(':')) // 2
        if emotes > self.config.values['emotes_max']:
            await self.error_and_delete(message, self.config.texts['emote_moderation'] % message.author.mention)


class Flomote(Module):
    async def on_message(self, message: discord.Message) -> None:
        content = message.content.lower()
        if content.startswith('flomote'):
            await message.channel.send(self.config.texts['flomote'])
        if content.startswith('floeyes'):
            await message.channel.send(self.config.texts['floeyes'])


class Help(Module):
    async def on_message(self, message: discord.Message) -> None:
        if message.content.lower().startswith('!help'):
            if message.channel.id != self.config.bots().id:
                await self.error_and_delete(message, self.config.texts['wrong_channel'] % ('!help', self.config.bots().mention))
                return
            args = message.content.split()
            if len(args) == 1:
                await self.error_and_delete(message, self.config.texts['help']['missing'])
                return
            try:
                await message.channel.send(self.config.texts['help']['command'][args[1]])
            except KeyError:
                await self.error_and_delete(message, self.config.texts['help']['invalid'] % args[1])


class Levels(Module):
    def __init__(self, config: Config):
        super().__init__(config, config.intervals['levels'])
        self.cooldowns = []
        base = self.config.values['level_base']
        multiplier = self.config.values['level_multiplier']
        self.levels = {0: 0, 1: base}
        for i in range(2, self.config.values['level_max']):
            self.levels[i] = int(self.levels[i - 1] + base * multiplier ** i)
        roles = self.config.roles['level']
        self.roles = {int(i): roles[i] for i in roles if i.isdigit()}

    @tasks.loop(minutes=1)
    async def run_schedule(self) -> None:
        self.cooldowns = []
        for vc in self.config.server().voice_channels:
            if len(vc.members) > 1 and vc.category_id != self.config.categories['tickets']:
                for member in vc.members:
                    if not member.voice.afk and ((not member.voice.mute and not member.voice.self_mute) or member.voice.self_stream):
                        self.award_level(member)

    async def on_message(self, message: discord.Message) -> None:
        content = message.content
        if content.startswith(('!leaderboard', '!lb')):
            args = content.split()
            lb = {}
            start = 0
            if len(args) == 1:
                lb = self.get_lb(min(self.config.values['leaderboard_default'], len(self.config.server().members) - 1))
            elif args[1].isdigit():
                lb = self.get_lb(min(int(args[1]), self.config.values['leaderboard_max'], len(self.config.server().members) - 1))
            elif '-' in args[1]:
                ints = args[1].split('-')
                if len(ints) == 2 and (i.isdigit for i in ints):
                    try:
                        start = max(1, int(ints[0]))
                        end = min(int(ints[1]), start + self.config.values['leaderboard_max'], len(self.config.server().members) - 1)
                        if start >= end:
                            await self.error_and_delete(message, self.config.texts['leaderboard']['invalid'])
                            return
                        lb = self.get_lb(end, start - 1)
                    except ValueError:
                        await self.error_and_delete(message, self.config.texts['leaderboard']['invalid'])
                        return
                else:
                    await self.error_and_delete(message, self.config.texts['leaderboard']['invalid'])
                    return
            text = ''
            for rank, key in enumerate(lb, start=1):
                text += self.config.texts['leaderboard']['row'] % (rank if start == 0 else rank + start - 1, self.config.member(key).mention, lb[key], await self.get_level(lb[key]))
            await message.channel.send(text)
        elif content.startswith(('!level', '!rank')):
            if message.channel.id == self.config.bots().id:
                args = content.split()
                if len(message.mentions) > 1 or len(args) > 2:
                    await self.error_and_delete(message, self.config.texts['level']['multiple_arguments'])
                    return
                else:
                    member = message.author if len(args) == 1 else await self.get_member_from_id_or_mention(args[1], message)
                    if member.id is None:
                        return
                amount = self.get_from_database(member.id)
                if not amount:
                    await message.channel.send(self.config.texts['level']['no_xp'] % member.mention)
                    return
                amount = amount[0][0]
                level = await self.get_level(amount)
                to_next = self.levels[level + 1] - amount
                rank = self.get_rank(member.id)
                if rank[1] is None:
                    await message.channel.send(self.config.texts['level']['success_1'] % (member.mention, level, amount, rank[0], member.mention, to_next))
                else:
                    await message.channel.send(self.config.texts['level']['success'] % (member.mention, level, amount, rank[0], member.mention, to_next, member.mention, rank[1]))
                for key in self.roles:
                    if level >= key:
                        await self.config.member(member.id).add_roles(self.config.role(self.roles[key]))
            else:
                await self.error_and_delete(message, self.config.texts['wrong_channel'] % ('!level', self.config.bots().mention))
            return
        if message.channel.id in self.config.channels['level']:
            self.award_level(message.author)

    async def on_ready(self) -> None:
        await super().on_ready()
        for i in [i for i in self.config.server().members if i.get_role(self.config.special_requirement_role().id)]:
            await i.remove_roles(self.config.special_role())
        special = random.choice([i for i in self.config.server().members if not self.config.is_team(i) and i.get_role(self.config.special_requirement_role().id)])
        await special.add_roles(self.config.special_role())
        await self.config.chat().send(self.config.texts['special_notification'] % special.mention)

    async def get_level(self, xp: int) -> int:
        for key in self.levels:
            value = self.levels[key]
            if xp < value:
                return key - 1
        return self.config.values['level_max']

    def get_lb(self, end: int, begin: int = 0) -> dict:
        lb = dict(self.config.database.execute('SELECT * FROM levels;'))
        result = {}
        for k in lb.keys():
            if self.config.member(k) is not None:
                result[k] = lb[k]
        return dict(sorted(result.items(), key=lambda x: x[1], reverse=True)[begin:end])

    def get_rank(self, member: int) -> tuple:
        value = self.get_from_database(member)
        if not value:
            return 0, None
        value = value[0][0]
        values = list(self.get_lb(len(self.config.server().members)).items())
        if values[0][1] == value:
            return 1, None
        for i in range(1, len(values)):
            if values[i][1] == value:
                return i + 1, values[i - 1][1] - value
        return len(values), values[len(values) - 1][1] - value

    def get_from_database(self, member: int) -> list[tuple]:
        return self.config.database.execute('SELECT amount FROM levels WHERE id = %s;', member)

    def award_level(self, member: discord.Member) -> None:
        if member not in self.cooldowns:
            self.cooldowns.append(member)
            amount = self.get_from_database(member.id)
            multiplier = 1
            if member.get_role(self.config.premium_role().id):
                multiplier *= self.config.values['level_boost_premium']
            if member.get_role(self.config.special_role().id):
                multiplier *= self.config.values['level_boost_special']
            if amount is None or len(amount) == 0:
                self.config.database.execute('INSERT INTO levels (id, amount) VALUES(%s, 1);', member.id)
            else:
                self.config.database.execute('UPDATE levels SET amount = %s WHERE id = %s;', amount[0][0] + int(random.randrange(self.config.values["level_give_min"], self.config.values["level_give_max"] + 1) * multiplier), member.id)


class LinkModeration(Module):
    async def on_message(self, message: discord.Message) -> None:
        if self.config.is_team(message.author):
            return
        content = message.content.lower()
        # noinspection HttpUrlsUsage
        if not any(s in content for s in ['http://', 'https://']):
            return
        if any(elem in content for elem in self.config.values['link_blacklist']):
            await self.error_and_delete(message, self.config.texts['link_moderation'] % message.author.mention)
        elif not any(elem in content for elem in self.config.values['link_whitelist']):
            await self.error_and_delete(message, self.config.texts['link_moderation'] % message.author.mention)


class Logger(Module):
    async def on_member_join(self, member: discord.Member) -> None:
        embed = self.embed(self.config.texts['logger']['guild_joined'])
        embed.add_field(name=self.config.texts['logger']['user'], value=str(member), inline=False)
        embed.add_field(name=self.config.texts['logger']['ping'], value=member.mention, inline=False)
        embed.add_field(name=self.config.texts['logger']['created'], value=self.get_readable_datetime(str(member.created_at)), inline=True)
        embed.set_thumbnail(url=member.display_avatar.url)
        await self.config.join_log().send(embed=embed)

    async def on_member_remove(self, member: discord.Member) -> None:
        embed = self.error_embed(title=self.config.texts['logger']['guild_left'])
        embed.add_field(name=self.config.texts['logger']['user'], value=str(member), inline=False)
        embed.add_field(name=self.config.texts['logger']['ping'], value=member.mention, inline=False)
        embed.add_field(name=self.config.texts['logger']['created'], value=self.get_readable_datetime(str(member.created_at)), inline=False)
        embed.add_field(name=self.config.texts['logger']['joined'], value=self.get_readable_datetime(str(member.joined_at)), inline=True)
        embed.set_thumbnail(url=member.display_avatar.url)
        await self.config.leave_log().send(embed=embed)

    async def on_member_update(self, before: discord.Member, after: discord.Member) -> None:
        if after.nick != before.nick:
            embed = self.embed(self.config.texts['logger']['nick_updated'])
            embed.add_field(name=self.config.texts['logger']['user'], value=str(before), inline=False)
            embed.add_field(name=self.config.texts['logger']['ping'], value=before.mention, inline=False)
            embed.add_field(name=self.config.texts['logger']['before'], value=before.nick, inline=False)
            embed.add_field(name=self.config.texts['logger']['after'], value=after.nick, inline=True)
            await self.config.member_log().send(embed=embed)
        if after.guild_avatar is not None and before.guild_avatar is None:
            embed = self.embed(self.config.texts['logger']['guild_avatar_added'])
            embed.add_field(name=self.config.texts['logger']['user'], value=str(before), inline=False)
            embed.add_field(name=self.config.texts['logger']['ping'], value=before.mention, inline=True)
            embed.set_image(url=after.guild_avatar.url)
            await self.config.member_log().send(embed=embed)
        if after.guild_avatar is None and before.guild_avatar is not None:
            embed = self.embed(self.config.texts['logger']['guild_avatar_updated'])
            embed.add_field(name=self.config.texts['logger']['user'], value=str(before), inline=False)
            embed.add_field(name=self.config.texts['logger']['ping'], value=before.mention, inline=True)
            embed.set_thumbnail(url=before.guild_avatar.url)
            await self.config.member_log().send(embed=embed)
        if after.guild_avatar != before.guild_avatar:
            embed = self.embed(self.config.texts['logger']['guild_avatar_updated'])
            embed.add_field(name=self.config.texts['logger']['user'], value=str(before), inline=False)
            embed.add_field(name=self.config.texts['logger']['ping'], value=before.mention, inline=True)
            embed.set_thumbnail(url=before.guild_avatar.url)
            embed.set_image(url=after.guild_avatar.url)
            await self.config.member_log().send(embed=embed)

    async def on_user_update(self, before: discord.User, after: discord.User) -> None:
        if str(after) != str(before):
            embed = self.embed(self.config.texts['logger']['name_updated'])
            embed.add_field(name=self.config.texts['logger']['ping'], value=before.mention, inline=False)
            embed.add_field(name=self.config.texts['logger']['before'], value=str(before), inline=False)
            embed.add_field(name=self.config.texts['logger']['after'], value=str(after), inline=True)
            await self.config.member_log().send(embed=embed)
        if after.global_name != before.global_name:
            embed = self.embed(self.config.texts['logger']['global_name_updated'])
            embed.add_field(name=self.config.texts['logger']['user'], value=str(before), inline=False)
            embed.add_field(name=self.config.texts['logger']['ping'], value=before.mention, inline=False)
            embed.add_field(name=self.config.texts['logger']['before'], value=before.global_name, inline=False)
            embed.add_field(name=self.config.texts['logger']['after'], value=after.global_name, inline=True)
            await self.config.member_log().send(embed=embed)
        if after.avatar.url != before.avatar.url:
            embed = self.embed(self.config.texts['logger']['avatar_updated'])
            embed.add_field(name=self.config.texts['logger']['user'], value=str(before), inline=False)
            embed.add_field(name=self.config.texts['logger']['ping'], value=before.mention, inline=True)
            embed.set_thumbnail(url=before.avatar.url)
            embed.set_image(url=after.avatar.url)
            await self.config.member_log().send(embed=embed)

    async def on_message_edit(self, before: discord.Message, after: discord.Message) -> None:
        old = before.content
        new = after.content
        if old != new:
            embed = self.embed(self.config.texts['logger']['message_edited'])
            embed.add_field(name=self.config.texts['logger']['user'], value=before.author.mention, inline=False)
            embed.add_field(name=self.config.texts['logger']['channel'], value=before.channel.mention, inline=False)
            embed.add_field(name=self.config.texts['logger']['before'], value=old, inline=False)
            embed.add_field(name=self.config.texts['logger']['after'], value=new, inline=True)
            await self.config.message_log().send(embed=embed)

    async def on_message_delete(self, message: discord.Message) -> None:
        embed = self.error_embed(self.config.texts['logger']['message_deleted'])
        embed.add_field(name=self.config.texts['logger']['user'], value=message.author.mention, inline=False)
        embed.add_field(name=self.config.texts['logger']['channel'], value=message.channel.mention, inline=False)
        embed.add_field(name=self.config.texts['logger']['message'], value=message.content, inline=True)
        await self.config.message_log().send(embed=embed)

    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState) -> None:
        if before.channel is not None and after.channel is not None:
            embed = self.embed(self.config.texts['logger']['voice_switched'])
            embed.add_field(name=self.config.texts['logger']['user'], value=member.mention, inline=False)
            embed.add_field(name=self.config.texts['logger']['before'], value=before.channel.name, inline=False)
            embed.add_field(name=self.config.texts['logger']['after'], value=after.channel.name, inline=True)
            await self.config.voice_log().send(embed=embed)
        elif before.channel is None and after.channel is not None:
            embed = self.embed(self.config.texts['logger']['voice_joined'])
            embed.add_field(name=self.config.texts['logger']['user'], value=member.mention, inline=False)
            embed.add_field(name=self.config.texts['logger']['channel'], value=after.channel.name, inline=True)
            await self.config.voice_log().send(embed=embed)
        elif before.channel is not None and after.channel is None:
            embed = self.error_embed(self.config.texts['logger']['voice_left'])
            embed.add_field(name=self.config.texts['logger']['user'], value=member.mention, inline=False)
            embed.add_field(name=self.config.texts['logger']['channel'], value=before.channel.name, inline=True)
            await self.config.voice_log().send(embed=embed)


# noinspection PyTypeChecker
class Moderation(Module):
    async def warn(self, member: discord.Member, reason: str, team_member: discord.User, channel: discord.TextChannel):
        now = datetime.now()
        self.config.database.execute('INSERT INTO warns (member, reason, time, team_member) VALUES(%s, %s, %s, %s);', member.id, reason, now, team_member.id)
        await channel.send(self.config.texts['moderation']['warn_success'] % (member.mention, reason, team_member.mention))
        await self.config.moderation_log().send(self.config.texts['moderation']['warn_success'] % (member.mention, reason, team_member.mention))
        databasecontents = self.config.database.execute('SELECT * FROM warns WHERE member = %s ORDER BY id;', member.id)
        active = 0
        for i in databasecontents:
            if (now - datetime.strptime(i[3][:19], '%Y-%m-%d %H:%M:%S')).days < self.config.values['warn_expire_days']:
                active += 1
        if active >= self.config.values['mute_warnings']:
            await self.timeout(member, self.config.values['mute_duration'], self.config.texts['moderation']['too_many_warnings'], self.config.client.user, channel)
        if active >= self.config.values['kick_warnings']:
            await self.kick(member, self.config.texts['moderation']['too_many_warnings'], self.config.client.user, channel)
        if active >= self.config.values['ban_warnings']:
            await self.ban(member, self.config.texts['moderation']['too_many_warnings'], self.config.client.user, channel)

    async def timeout(self, member: discord.Member, duration: int, reason: str, team_member: discord.User, channel: discord.TextChannel) -> None:
        await member.timeout(datetime.now().astimezone() + timedelta(seconds=duration), reason=reason)
        await channel.send(self.config.texts['moderation']['mute_success'] % (member.mention, reason, team_member.mention))
        await self.config.moderation_log().send(self.config.texts['moderation']['mute_success'] % (member.mention, reason, team_member.mention))
        await member.add_roles(self.config.muted_role())

    async def kick(self, member: discord.Member, reason: str, team_member: discord.User, channel: discord.TextChannel) -> None:
        await member.kick(reason=reason)
        await channel.send(self.config.texts['moderation']['kick_success'] % (member.mention, reason, team_member.mention))
        await self.config.moderation_log().send(self.config.texts['moderation']['kick_success'] % (member.mention, reason, team_member.mention))

    async def ban(self, member: discord.Member, reason: str, team_member: discord.User, channel: discord.TextChannel) -> None:
        await member.ban(reason=reason, delete_message_days=1)
        await channel.send(self.config.texts['moderation']['ban_success'] % (member.mention, reason, team_member.mention))
        await self.config.moderation_log().send(self.config.texts['moderation']['ban_success'] % (member.mention, reason, team_member.mention))

    async def on_message(self, message: discord.Message) -> None:
        args = message.content.split()
        args[0] = args[0].lower()
        if args[0] == '!warn':
            if not self.config.is_team(message.author):
                await self.error_and_delete(message, self.config.texts['team_only'])
                return
            if len(args) < 3:
                await self.error_and_delete(message, self.config.texts['moderation']['warn_failure'])
                return
            member = await self.get_non_team_member_from_id_or_mention(args[1], message)
            if member is None:
                return
            await self.warn(member, ' '.join(args[2:]), message.author, message.channel)
        elif args[0] == '!removewarn':
            if not self.config.is_team(message.author):
                await self.error_and_delete(message, self.config.texts['team_only'])
                return
            if len(args) < 2:
                await self.error_and_delete(message, self.config.texts['moderation']['removewarn_failure'])
                return
            try:
                warn = int(args[1])
            except ValueError:
                await self.error_and_delete(message, self.config.texts['moderation']['removewarn_failure'])
                return
            self.config.database.execute('DELETE FROM warns WHERE id = %s;', warn)
            await message.channel.send(self.config.texts['moderation']['removewarn_success'] % warn)
            await self.config.moderation_log().send(self.config.texts['moderation']['removewarn_success'] % warn)
        elif args[0] == '!warnings':
            if message.channel.id != self.config.bots().id:
                await self.error_and_delete(message, self.config.texts['wrong_channel'] % ('!warnings', self.config.bots().mention))
                return
            if len(message.mentions) > 1:
                await self.error_and_delete(message, self.config.texts['moderation']['multiple_arguments'])
                return
            member = message.author if len(args) == 1 else await self.get_member_from_id_or_mention(args[1], message)
            if member is None:
                return
            databasecontents = self.config.database.execute('SELECT * FROM warns WHERE member = %s ORDER BY id;', member.id)
            result = self.config.texts['moderation']['warnings_success'] % member.mention
            if not databasecontents:
                result += self.config.texts['moderation']['warnings_none']
            else:
                for i in databasecontents:
                    result += self.config.texts['moderation']['warnings_item'] % (self.get_readable_datetime(i[3]), i[2], self.config.member(i[4]).mention, i[0])
                    if (datetime.now() - datetime.strptime(i[3][:19], '%Y-%m-%d %H:%M:%S')).days >= self.config.values['warn_expire_days']:
                        result += self.config.texts['moderation']['warnings_expired']
            await message.channel.send(result)
        elif args[0] == '!mute':
            if not self.config.is_team(message.author):
                await self.error_and_delete(message, self.config.texts['team_only'])
                return
            if len(args) < 4:
                await self.error_and_delete(message, self.config.texts['moderation']['mute_failure'])
                return
            member = await self.get_non_team_member_from_id_or_mention(args[1], message)
            if member is not None:
                await self.timeout(member, self.get_duration(args[2]), ' '.join(args[3:]), self.config.client.user, message.channel)
        elif args[0] == '!unmute':
            if not self.config.is_team(message.author):
                await self.error_and_delete(message, self.config.texts['team_only'])
                return
            if len(args) < 2:
                await self.error_and_delete(message, self.config.texts['moderation']['unmute_failure'])
                return
            member = await self.get_non_team_member_from_id_or_mention(args[1], message)
            if member is not None:
                reason = self.config.texts['moderation']['no_reason'] if len(args) == 2 else ' '.join(args[2:])
                await member.timeout(None, reason=reason)
                await message.channel.send(self.config.texts['moderation']['unmute_success'] % (member.mention, reason, message.author.mention))
                await self.config.moderation_log().send(self.config.texts['moderation']['unmute_success'] % (member.mention, reason, message.author.mention))
        elif args[0] == '!kick':
            if not self.config.is_team(message.author):
                await self.error_and_delete(message, self.config.texts['team_only'])
                return
            if len(args) < 3:
                await self.error_and_delete(message, self.config.texts['moderation']['kick_failure'])
                return
            member = await self.get_non_team_member_from_id_or_mention(args[1], message)
            if member is not None:
                await self.kick(member, ' '.join(args[2:]), self.config.client.user, message.channel)
        elif args[0] == '!ban':
            if not self.config.is_team(message.author):
                await self.error_and_delete(message, self.config.texts['team_only'])
                return
            if len(args) < 3:
                await self.error_and_delete(message, self.config.texts['moderation']['ban_failure'])
                return
            member = await self.get_non_team_member_from_id_or_mention(args[1], message)
            if member is not None:
                await self.ban(member, ' '.join(args[2:]), self.config.client.user, message.channel)
        else:
            if self.config.is_team(message.author):
                return
            blacklist = set(self.config.values['ping_blacklist'])
            for member in message.mentions:
                if member.id in blacklist:
                    await self.warn(message.author, self.config.texts['moderation']['ping_reason'], self.config.client.user, message.channel)
                    await message.delete()


class Ping(Module):
    async def on_message(self, message: discord.Message) -> None:
        if message.content.lower().startswith('!ping'):
            created_at = message.created_at
            now = datetime.now(timezone.utc)
            time = str(now - created_at) if now > created_at else str(created_at - now)
            if time.startswith('0:00:'):
                time = time[5:]
            if time.startswith('00'):
                time = time[1:]
            await message.channel.send(self.config.texts['ping'] % time)


class PrankMute(Module):
    async def on_message(self, message: discord.Message) -> None:
        args = message.content.split()
        if args[0].lower() == '?mute':
            if not message.author.get_role(self.config.prank_mute_requirement_role().id):
                await self.error_and_delete(message, self.config.texts['prank_mute']['failure'])
                return
            if len(args) == 1:
                await self.error_and_delete(message, self.config.texts['prank_mute']['missing_user'])
                return
            if len(args) == 2:
                await self.error_and_delete(message, self.config.texts['prank_mute']['missing_reason'])
                return
            member = await self.get_member_from_id_or_mention(args[1], message)
            if member is None:
                return
            reason = ' '.join(args[2:])
            await member.timeout(datetime.now().astimezone() + timedelta(seconds=86400), reason=reason)
            await message.channel.send(self.config.texts['prank_mute']['start'] % (member.mention, reason, message.author.mention), delete_after=self.config.values['prank_mute_duration'])
            await asyncio.sleep(self.config.values['prank_mute_duration'])
            await member.timeout(None)
            await message.channel.send(self.config.texts['prank_mute']['end'])


class RawEcho(Module):
    async def on_message(self, message: discord.Message) -> None:
        content = message.content.lower()
        if content.startswith('!rawecho '):
            await message.channel.send(f'`{content[len("!rawecho "):]}`')


class Reload(Module):
    async def on_message(self, message: discord.Message) -> None:
        if message.content.lower().startswith('!reload') and self.config.is_team(message.author):
            await message.channel.send(self.config.texts['reload']['start'])
            self.config.load()
            await message.channel.send(self.config.texts['reload']['end'])


class RockPaperScissors(Module):
    def __init__(self, config: Config):
        super().__init__(config)
        self.players = []

    async def on_message(self, message: discord.Message) -> None:
        content = message.content.lower()
        if content.startswith('!ssp') and message.author.id not in self.players:
            self.players.append(message.author.id)
            await message.channel.send(self.config.texts['rps']['start'])
        elif message.author.id in self.players:
            self.players.remove(message.author.id)
            if content.startswith(self.config.texts['rps']['rock'].lower()):
                result = self.get_result(0)
            elif content.startswith(self.config.texts['rps']['paper'].lower()):
                result = self.get_result(1)
            elif content.startswith(self.config.texts['rps']['scissors'].lower()):
                result = self.get_result(2)
            else:
                result = self.config.texts['rps']['invalid']
            await message.channel.send(result)

    def get_result(self, prompt: int) -> str:
        choice = random.choice([0, 1, 2])
        texts = [self.config.texts['rps']['rock'], self.config.texts['rps']['paper'], self.config.texts['rps']['scissors']]
        if (prompt == 0 and choice == 1) or (prompt == 1 and choice == 2) or (prompt == 2 and choice == 0):
            return self.config.texts['rps']['result'] % (texts[prompt], texts[choice], self.config.texts['rps']['lose'])
        elif (prompt == 1 and choice == 0) or (prompt == 2 and choice == 1) or (prompt == 0 and choice == 2):
            return self.config.texts['rps']['result'] % (texts[prompt], texts[choice], self.config.texts['rps']['win'])
        else:
            return self.config.texts['rps']['result'] % (texts[prompt], texts[choice], self.config.texts['rps']['draw'])


class Roles(Module):
    async def on_message(self, message: discord.Message) -> None:
        content = message.content.lower()
        if content.startswith('!videos'):
            if message.channel.id != self.config.bots().id:
                await self.error_and_delete(message, self.config.texts['wrong_channel'] % ('!videos', self.config.bots().mention))
                return
            await message.author.add_roles(self.config.video_role())
            await message.channel.send(self.config.texts['roles']['videos'])
        elif content.startswith('!keinevideos'):
            if message.channel.id != self.config.bots().id:
                await self.error_and_delete(message, self.config.texts['wrong_channel'] % ('!keinevideos', self.config.bots().mention))
                return
            await message.author.remove_roles(self.config.video_role())
            await message.channel.send(self.config.texts['roles']['keinevideos'])
        elif self.config.is_team(message.author):
            if content.startswith('!chatsupport'):
                await message.author.add_roles(self.config.chat_support_role())
                await message.channel.send(self.config.texts['roles']['chatsupport'])
            elif content.startswith('!keinchatsupport'):
                await message.author.remove_roles(self.config.chat_support_role())
                await message.channel.send(self.config.texts['roles']['keinchatsupport'])
            elif content.startswith('!voicesupport'):
                await message.author.add_roles(self.config.voice_support_role())
                await message.channel.send(self.config.texts['roles']['voicesupport'])
            elif content.startswith('!keinvoicesupport'):
                await message.author.remove_roles(self.config.voice_support_role())
                await message.channel.send(self.config.texts['roles']['keinvoicesupport'])


class Rules(Module):
    def __init__(self, config: Config):
        super().__init__(config, config.intervals['rules'])
        self.messages = 0

    @tasks.loop(seconds=1)
    async def run_schedule(self):
        if self.messages > int(self.config.values['rules_limit']):
            await self.send_message()

    async def send_message(self) -> None:
        await self.config.chat().send(self.config.texts['rules'] % (self.config.rules().mention, self.config.short_rules().mention))
        self.messages = 0

    async def on_message(self, message: discord.Message) -> None:
        if message.channel.id == self.config.chat().id:
            self.messages += 1
        if message.content.lower().startswith('!regeln'):
            await self.send_message()


class SelfDestruct(Module):
    async def on_message(self, message: discord.Message) -> None:
        if message.content.lower().startswith('!selbstzerstörung'):
            msg = await message.channel.send(embed=self.make_embed('text_3'))
            await asyncio.sleep(1)
            await msg.edit(embed=self.make_embed('text_2'))
            await asyncio.sleep(1)
            await msg.edit(embed=self.make_embed('text_1'))
            await asyncio.sleep(1)
            await msg.edit(embed=self.make_embed('text_0'))
            await message.channel.send(self.config.texts['self_destruct']['image_0'])

    def make_embed(self, text_id: str) -> discord.Embed:
        embed = self.embed(self.config.texts['self_destruct']['title'])
        embed.set_thumbnail(url=self.config.texts['self_destruct']['image_1'])
        embed.add_field(name=self.config.texts['self_destruct'][text_id], value='', inline=True)
        return embed


class Slowmode(Module):
    def __init__(self, config: Config):
        super().__init__(config, config.intervals['slowmode'])
        self.messages = 0

    @tasks.loop(seconds=1)
    async def run_schedule(self):
        if self.messages > 15:
            await self.config.chat().edit(slowmode_delay=15)
        elif self.messages > 10:
            await self.config.chat().edit(slowmode_delay=10)
        elif self.messages > 5:
            await self.config.chat().edit(slowmode_delay=5)
        else:
            await self.config.chat().edit(slowmode_delay=0)
        self.messages = 0

    async def on_message(self, message: discord.Message) -> None:
        if message.channel.id == self.config.chat().id:
            self.messages += 1


class TempVoice(Module):
    def __init__(self, config: Config):
        super().__init__(config, config.intervals['temp_voice'])
        self.channels = {}

    @tasks.loop(seconds=1)
    async def run_schedule(self):
        for vc in self.config.server().voice_channels:
            if vc.category_id == self.config.voice_category().id and vc.id != self.config.afk().id and vc.id != self.config.voice_join().id and vc.id != self.config.voice_move().id and not vc.members:
                await vc.delete()

    async def on_message(self, message: discord.Message) -> None:
        content = message.content
        if content.lower().startswith('!vc '):
            if message.channel.id != self.config.bots().id:
                await self.error_and_delete(message, self.config.texts['wrong_channel'] % ('!vc', self.config.bots().mention))
                return
            if message.author.id not in self.channels:
                await self.error_and_delete(message, self.config.texts['temp_voice']['failure'])
                return
            args = content.split()
            if args[1].lower() == 'show':
                await self.channels[message.author.id].set_permissions(target=self.config.default_role(), view_channel=True)
                await message.channel.send(self.config.texts['temp_voice']['show'])
                await self.config.voice_log().send(self.config.texts['temp_voice']['show_log'] % message.author.id)
            elif args[1].lower() == 'hide':
                await self.channels[message.author.id].set_permissions(target=self.config.default_role(), view_channel=False)
                await message.channel.send(self.config.texts['temp_voice']['hide'])
                await self.config.voice_log().send(self.config.texts['temp_voice']['hide_log'] % message.author.id)
            elif args[1].lower() == 'open':
                await self.channels[message.author.id].set_permissions(target=self.config.default_role(), connect=True)
                await message.channel.send(self.config.texts['temp_voice']['open'])
                await self.config.voice_log().send(self.config.texts['temp_voice']['open_log'] % message.author.id)
            elif args[1].lower() == 'close':
                await self.channels[message.author.id].set_permissions(target=self.config.default_role(), connect=False)
                await message.channel.send(self.config.texts['temp_voice']['close'])
                await self.config.voice_log().send(self.config.texts['temp_voice']['close_log'] % message.author.id)
            elif args[1].lower() == 'limit':
                if len(args) == 2:
                    await self.error_and_delete(message, self.config.texts['temp_voice']['limit_missing'])
                    return
                try:
                    limit = int(args[2])
                except TypeError:
                    await self.error_and_delete(message, self.config.texts['temp_voice']['limit_failure'])
                    return
                if limit < 0 or limit > 99:
                    await self.error_and_delete(message, self.config.texts['temp_voice']['limit_failure'])
                    return
                await self.channels[message.author.id].edit(user_limit=limit)
                await message.channel.send(self.config.texts['temp_voice']['limit_success'] % limit)
                await self.config.voice_log().send(self.config.texts['temp_voice']['limit_log'] % (message.author.id, limit))
            elif args[1].lower() == 'name':
                if len(args) == 2:
                    await self.error_and_delete(message, self.config.texts['temp_voice']['name_failure'])
                    return
                name = ' '.join(args[2:])
                await self.channels[message.author.id].edit(name=self.config.texts['temp_voice']['name'] % name)
                await message.channel.send(self.config.texts['temp_voice']['name_success'] % name)
                await self.config.voice_log().send(self.config.texts['temp_voice']['name_log'] % (message.author.id, name))
            else:
                await self.error_and_delete(message, self.config.texts['temp_voice']['invalid'] % args[1])

    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState) -> None:
        if after.channel == self.config.voice_join():
            if member.id not in self.channels:
                await self.get_channel(member)
            await member.move_to(self.channels[member.id])

    async def get_channel(self, member: discord.Member) -> None:
        try:
            self.channels[member.id] = await self.config.server().create_voice_channel(self.config.texts['temp_voice']['name'] % member.display_name, category=self.config.voice_category(), overwrites={
                self.config.server().default_role: discord.PermissionOverwrite(view_channel=False, connect=False),
                self.config.default_role(): discord.PermissionOverwrite(view_channel=True, connect=True),
                self.config.server().get_role(self.config.roles['test_supporter']): discord.PermissionOverwrite(view_channel=True, connect=True),
                self.config.server().get_role(self.config.roles['supporter']): discord.PermissionOverwrite(view_channel=True, connect=True),
                self.config.server().get_role(self.config.roles['test_moderator']): discord.PermissionOverwrite(view_channel=True, connect=True),
                self.config.server().get_role(self.config.roles['moderator']): discord.PermissionOverwrite(view_channel=True, connect=True),
                self.config.server().get_role(self.config.roles['head_moderator']): discord.PermissionOverwrite(view_channel=True, connect=True),
                self.config.server().get_role(self.config.roles['test_administrator']): discord.PermissionOverwrite(view_channel=True, connect=True),
                member: discord.PermissionOverwrite(move_members=True)
            })
            await asyncio.sleep(1)
        except discord.HTTPException:
            await asyncio.sleep(1)
            await self.get_channel(member)


class Tickets(Module):
    async def on_message(self, message: discord.Message) -> None:
        content = message.content.lower()
        if content.startswith('!ticket'):
            if message.channel.id == self.config.channels['tickets']:
                ticket = self.config.database.execute('SELECT channel FROM tickets WHERE owner = %s', message.author.id)
                if ticket:
                    await self.error_and_delete(message, self.config.texts['tickets']['ticket_failure'] % self.config.text_channel(ticket[0][0]))
                    return
                self.config.database.execute('INSERT INTO tickets (channel, owner) VALUES(%s, %s);', 0, message.author.id)
                ticket = await self.config.server().create_text_channel(name=self.config.texts['tickets']['name'] % self.config.database.execute('SELECT id FROM tickets WHERE owner = %s;', message.author.id), category=self.config.tickets_category(), overwrites={
                    self.config.server().default_role: discord.PermissionOverwrite(read_messages=False),
                    self.config.server().me: discord.PermissionOverwrite(read_messages=True),
                    message.author: discord.PermissionOverwrite(read_messages=True),
                    self.config.role(self.config.roles['test_supporter']): discord.PermissionOverwrite(read_messages=True),
                    self.config.role(self.config.roles['supporter']): discord.PermissionOverwrite(read_messages=True),
                    self.config.role(self.config.roles['test_moderator']): discord.PermissionOverwrite(read_messages=True),
                    self.config.role(self.config.roles['moderator']): discord.PermissionOverwrite(read_messages=True),
                    self.config.role(self.config.roles['head_moderator']): discord.PermissionOverwrite(read_messages=True),
                    self.config.role(self.config.roles['test_administrator']): discord.PermissionOverwrite(read_messages=True)
                })
                self.config.database.execute('UPDATE tickets SET channel = %s WHERE owner = %s;', ticket.id, message.author.id)
                await ticket.send(self.config.texts['tickets']['ticket_success'] % (self.config.chat_support_role().mention, message.author.mention))
            else:
                await self.error_and_delete(message, self.config.texts['wrong_channel'] % ('!ticket', self.config.tickets().mention))
                return
        elif message.channel.id == self.config.channels['tickets']:
            await self.error_and_delete(message, self.config.texts['tickets']['ticket_invalid'])
            return
        if content.startswith('!close'):
            if any(i[0] == message.channel.id for i in self.config.database.execute('SELECT channel FROM tickets;')):
                ticket = self.config.database.execute('SELECT owner FROM tickets WHERE channel = %s;', message.channel.id)
                await message.channel.set_permissions(target=self.config.member(ticket[0][0]), read_messages=False)
                await message.channel.send(self.config.texts['tickets']['close_success'])
            else:
                await self.error_and_delete(message, self.config.texts['tickets']['close_wrong_channel'])
                return
        if content.startswith('!delete'):
            if not any(i[0] == message.channel.id for i in self.config.database.execute('SELECT channel FROM tickets;')):
                await self.error_and_delete(message, self.config.texts['tickets']['delete_wrong_channel'])
                return
            elif not self.config.is_team(message.author):
                await self.error_and_delete(message, self.config.texts['team_only'])
                return
            else:
                self.config.database.execute('DELETE FROM tickets WHERE channel = %s;', message.channel.id)
                await self.config.text_channel(message.channel.id).delete()


class Tricks(Module):
    def __init__(self, config: Config):
        super().__init__(config)
        self.tricks = {}

    async def on_message(self, message: discord.Message) -> None:
        content = message.content.lower()
        if content.startswith('!'):
            if content.startswith('!addtrick'):
                if not self.config.is_team(message.author):
                    await self.error_and_delete(message, self.config.texts['team_only'])
                    return
                split = message.content.split()
                if len(split) > 2:
                    name = split[1].lower()
                    text = message.content.replace('!addtrick ' + name + ' ', '')
                    self.config.database.execute('INSERT INTO tricks (id, text) VALUES(%s, %s);', name, text)
                    self.tricks[name] = text
                    await message.channel.send((self.config.texts['tricks']['added'] % name) + text)
            elif content.startswith('!removetrick'):
                if not self.config.is_team(message.author):
                    await self.error_and_delete(message, self.config.texts['team_only'])
                    return
                split = message.content.split()
                if len(split) > 1:
                    name = split[1].lower()
                    self.config.database.execute('DELETE FROM tricks WHERE id = %s;', name)
                    self.tricks.pop(name)
                    await message.channel.send(self.config.texts['tricks']['removed'] % name)
            elif content.startswith('!tricks'):
                if message.channel.id != self.config.bots().id:
                    await self.error_and_delete(message, self.config.texts['wrong_channel'] % ('!tricks', self.config.bots().mention))
                    return
                tricklist = '\n'.join(['!' + elem for elem in self.tricks.keys()])
                if tricklist:
                    await message.channel.send(self.config.texts['tricks']['list'] + self.config.texts['tricks']['none'])
                else:
                    await message.channel.send(self.config.texts['tricks']['list'] + tricklist)
            else:
                name = content.split()[0][1:]
                if name in self.tricks:
                    await message.channel.send('**!' + name + '**\n\n' + self.tricks[name])

    async def on_ready(self) -> None:
        await super().on_ready()
        for elem in self.config.database.execute('SELECT id, text FROM tricks;'):
            self.tricks[elem[0]] = elem[1]


class UserInfo(Module):
    async def on_message(self, message: discord.Message) -> None:
        content = message.content.lower()
        if content.startswith('!userinfo'):
            if message.channel.id != self.config.bots().id:
                await self.error_and_delete(message, self.config.texts['wrong_channel'] % ('!userinfo', self.config.bots().mention))
                return
            args = content.split()
            if len(message.mentions) > 1 or len(args) > 2:
                await self.error_and_delete(message, self.config.texts['userinfo']['multiple_arguments'])
                return
            member = message.author if len(args) == 1 else await self.get_member_from_id_or_mention(args[1], message)
            if member is None:
                return
            embed = self.embed(member.display_name).set_thumbnail(url=member.avatar)
            embed.add_field(name=self.config.texts['userinfo']['member'], value=member.name + '#' + member.discriminator, inline=False)
            embed.add_field(name=self.config.texts['userinfo']['id'], value=member.id, inline=False)
            embed.add_field(name=self.config.texts['userinfo']['mention'], value=member.mention, inline=False)
            embed.add_field(name=self.config.texts['userinfo']['account_created'], value=self.get_readable_datetime(str(member.created_at)), inline=False)
            embed.add_field(name=self.config.texts['userinfo']['guild_joined'], value=self.get_readable_datetime(str(member.joined_at)), inline=False)
            premium = member.premium_since
            if premium is not None:
                embed.add_field(name=self.config.texts['userinfo']['booster_since'], value=self.get_readable_datetime(str(premium)), inline=False)
            await message.channel.send(embed=embed)


class VoiceSupport(Module):
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState) -> None:
        if after.channel is not None and after.channel.id == self.config.voice_support().id:
            await self.config.team_voice_support().send(self.config.texts['voice_support'] % (self.config.voice_support_role().mention, member.mention))


class Write(Module):
    async def on_message(self, message: discord.Message) -> None:
        if message.content.startswith('!write ') and self.config.is_team(message.author):
            args = message.content.split()
            if args[1].startswith('<#') and args[1].endswith('>'):
                args[1] = args[1][2:-1]
            try:
                await self.config.text_channel(int(args[1])).send(' '.join(args[2:]))
            except ValueError:
                await self.error_and_delete(message, self.config.texts['invalid_channel'])
