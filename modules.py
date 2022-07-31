import random
from datetime import datetime

import discord
from discord.ext import tasks

from config import Config
from module import Module


class AmongUs(Module):
    def __init__(self, config: Config):
        super().__init__(config)
        self.message = None
        self.reactions = {}
        self.order = []
        self.impostor = None
        self.crewmate1 = None
        self.crewmate2 = None
        self.votes = [0, 0, 0]

    @tasks.loop(seconds=1)
    async def run_schedule(self):
        members = list(self.config.get_server().members)
        self.impostor = members[random.randint(0, len(members) - 1)]
        members.remove(self.impostor)
        self.crewmate1 = members[random.randint(0, len(members) - 1)]
        members.remove(self.crewmate1)
        self.crewmate2 = members[random.randint(0, len(members) - 1)]
        members.remove(self.crewmate2)
        self.order = [self.impostor, self.crewmate1, self.crewmate2]
        random.shuffle(self.order)
        self.message = await self.config.get_chat().send(self.config.texts['among_us']['start'] % (self.config.values['among_us_reward'], self.config.values['among_us_crewmate'], self.config.values['among_us_crewmate'], self.config.values['among_us_limit'], self.order[0].display_name, self.order[1].display_name, self.order[2].display_name))
        await self.message.add_reaction('1️⃣')
        await self.message.add_reaction('2️⃣')
        await self.message.add_reaction('3️⃣')
        self.run_schedule.change_interval(seconds=self.config.delays['among_us'] + 2 * random.randint(0, self.config.delays['among_us']) - self.config.delays['among_us_offset'])

    async def on_reaction_add(self, reaction: discord.Reaction, member: discord.Member) -> None:
        if self.message is None or self.message.id != reaction.message.id:
            return
        if reaction.emoji != '1️⃣' and reaction.emoji != '2️⃣' and reaction.emoji != '3️⃣':
            return
        if self.reactions.get(member.id) is not None:
            await reaction.message.remove_reaction(self.reactions.get(member.id), member)
        if reaction.emoji == '1️⃣':
            self.votes[0] += 1
            self.reactions[member.id] = 0
        if reaction.emoji == '2️⃣':
            self.votes[1] += 1
            self.reactions[member.id] = 1
        if reaction.emoji == '3️⃣':
            self.votes[2] += 1
            self.reactions[member.id] = 2
        if len(self.reactions) == self.config.values['among_us_limit']:
            index = None
            if self.votes[0] > self.votes[1] and self.votes[0] > self.votes[2]:
                index = self.votes[0]
            if self.votes[1] > self.votes[0] and self.votes[1] > self.votes[2]:
                index = self.votes[1]
            if self.votes[2] > self.votes[0] and self.votes[2] > self.votes[1]:
                index = self.votes[2]
            if index is None:
                username = self.config.texts['among_us']['none']
            else:
                username = self.order[index].display_name
            users = []
            usernames = ''
            for key, value in self.reactions:
                if value == index:
                    users.append(key)
                    usernames += ', ' + self.config.get_member(key).display_name
            await reaction.message.channel.send(self.config.texts['among_us']['end'] % (username, self.impostor.display_name, usernames[2:]))
            # TODO levelling
            self.message = None
            self.reactions = {}
            self.order = []
            self.impostor = None
            self.crewmate1 = None
            self.crewmate2 = None
            self.votes = [0, 0, 0]

    async def on_reaction_remove(self, reaction: discord.Reaction, member: discord.Member) -> None:
        if self.message is None or self.message.id != reaction.message.id:
            return
        if reaction.emoji != '1️⃣' and reaction.emoji != '2️⃣' and reaction.emoji != '3️⃣':
            return
        if reaction.emoji == '1️⃣':
            self.votes[0] -= 1
            if self.reactions.get(member.id) == 0:
                self.reactions.pop(member.id)
        if reaction.emoji == '2️⃣':
            self.votes[1] -= 1
            if self.reactions.get(member.id) == 1:
                self.reactions.pop(member.id)
        if reaction.emoji == '3️⃣':
            self.votes[2] -= 1
            if self.reactions.get(member.id) == 2:
                self.reactions.pop(member.id)

    async def on_ready(self) -> None:
        self.run_schedule.change_interval(seconds=self.config.delays['among_us'] + 2 * random.randint(0, self.config.delays['among_us']) - self.config.delays['among_us_offset'])
        self.run_schedule.start()


class Clear(Module):
    async def on_message(self, message: discord.Message) -> None:
        content = str(message.content).lower()
        if str(message.content).lower().startswith('!clear '):
            if self.config.is_team(message.author):
                strings = content.split(' ')
                if len(strings) > 1 and strings[1].isnumeric():
                    async for m in message.channel.history(limit=int(strings[1])):
                        await m.delete()
            else:
                await message.channel.send(self.config.texts['team_only'], delete_after=self.config.values['delete_after'])


class Counter(Module):
    async def on_message(self, message: discord.Message) -> None:
        content = str(message.content).lower()
        if ' ' in content:
            return
        variable = None
        amount = 0
        if content.endswith('='):
            variable = content.replace('=', '')
            result = self.config.database.execute('SELECT value FROM counters WHERE id = \'' + variable + '\';')
            await message.channel.send(variable + ' = ' + str(result[0][0]))
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
        if variable is not None and amount != 0:
            old = self.config.database.execute('SELECT value FROM counters WHERE id = \'' + variable + '\';')
            if len(old) == 0:
                self.config.database.execute('INSERT INTO counters (id, value) VALUES(\'' + variable + '\', ' + str(amount) + ');')
            else:
                amount += old[0][0]
                self.config.database.execute('UPDATE counters SET value = ' + str(amount) + ' WHERE id = \'' + variable + '\';')
            result = self.config.database.execute('SELECT value FROM counters WHERE id = \'' + variable + '\';')
            await message.channel.send(variable + ' = ' + str(result[0][0]))


class Creeper(Module):
    async def on_message(self, message: discord.Message) -> None:
        if str(message.content).startswith('!creeper') or str(message.content).startswith('creeper') or str(message.content).startswith('creper'):
            await message.channel.send(self.config.texts['creeper'])


class Flomote(Module):
    async def on_message(self, message: discord.Message) -> None:
        if str(message.content).lower().startswith('flomote'):
            await message.channel.send(self.config.texts['flomote'])
        if str(message.content).lower().startswith('floeyes'):
            await message.channel.send(self.config.texts['floeyes'])


class Logger(Module):
    async def on_member_join(self, member: discord.Member) -> None:
        embed = self.embed(self.config.texts['logger']['guild_joined'])
        embed.add_field(name=self.config.texts['logger']['user'], value=member.mention, inline=False)
        embed.add_field(name=self.config.texts['logger']['created'], value=member.created_at, inline=True)
        await self.config.get_join_log().send(embed=embed)

    async def on_member_remove(self, member: discord.Member) -> None:
        embed = self.error_embed(title=self.config.texts['logger']['guild_left'])
        embed.add_field(name=self.config.texts['logger']['user'], value=member.mention, inline=False)
        embed.add_field(name=self.config.texts['logger']['created'], value=member.created_at, inline=False)
        embed.add_field(name=self.config.texts['logger']['joined'], value=member.joined_at, inline=True)
        await self.config.get_leave_log().send(embed=embed)

    async def on_message_edit(self, before: discord.Message, after: discord.Message) -> None:
        embed = self.embed(self.config.texts['logger']['message_edited'])
        old = str(before.content)
        new = str(after.content)
        if old != new:
            embed.add_field(name=self.config.texts['logger']['user'], value=before.author.mention, inline=False)
            embed.add_field(name=self.config.texts['logger']['channel'], value=before.channel.mention, inline=False)
            embed.add_field(name=self.config.texts['logger']['before'], value=old, inline=False)
            embed.add_field(name=self.config.texts['logger']['after'], value=new, inline=True)
            await self.config.get_message_log().send(embed=embed)

    async def on_message_delete(self, message: discord.Message) -> None:
        embed = self.error_embed(self.config.texts['logger']['message_deleted'])
        embed.add_field(name=self.config.texts['logger']['user'], value=message.author.mention, inline=False)
        embed.add_field(name=self.config.texts['logger']['channel'], value=message.channel.mention, inline=False)
        embed.add_field(name=self.config.texts['logger']['message'], value=message.content, inline=True)
        await self.config.get_message_log().send(embed=embed)

    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState) -> None:
        if before.channel is not None and after.channel is not None:
            embed = self.embed(self.config.texts['logger']['voice_switched'])
            embed.add_field(name=self.config.texts['logger']['user'], value=member.mention, inline=False)
            embed.add_field(name=self.config.texts['logger']['before'], value=before.channel.name, inline=False)
            embed.add_field(name=self.config.texts['logger']['after'], value=after.channel.name, inline=True)
            await self.config.get_voice_log().send(embed=embed)
        elif before.channel is None and after.channel is not None:
            embed = self.embed(self.config.texts['logger']['voice_joined'])
            embed.add_field(name=self.config.texts['logger']['user'], value=member.mention, inline=False)
            embed.add_field(name=self.config.texts['logger']['channel'], value=after.channel.name, inline=True)
            await self.config.get_voice_log().send(embed=embed)
        elif before.channel is not None and after.channel is None:
            embed = self.error_embed(self.config.texts['logger']['voice_left'])
            embed.add_field(name=self.config.texts['logger']['user'], value=member.mention, inline=False)
            embed.add_field(name=self.config.texts['logger']['channel'], value=before.channel.name, inline=True)
            await self.config.get_voice_log().send(embed=embed)


class Moderation(Module):
    @staticmethod
    async def timeout(member: discord.Member, duration: int, reason: str) -> None:
        # TODO
        pass

    @staticmethod
    async def kick(member: discord.Member, reason: str) -> None:
        await member.kick(reason=reason)

    @staticmethod
    async def ban(member: discord.Member, reason: str) -> None:
        await member.ban(reason=reason, delete_message_days=0)

    async def on_message(self, message: discord.Message) -> None:
        if not str(message.content).startswith('!'):
            return
        if not self.config.is_team(message.author):
            await message.channel.send(self.config.texts['team_only'], delete_after=self.config.values['delete_after'])
            await message.delete(delay=self.config.values['delete_after'])
            return
        args = str(message.content).split(' ')
        args[0] = args[0].lower()[1:]
        if args[0] == 'warn':
            if len(args) < 3:
                await message.channel.send(self.config.texts['moderation']['warn_failure'], delete_after=self.config.values['delete_after'])
                await message.delete(delay=self.config.values['delete_after'])
                return
            member = await self.get_non_team_member_from_id_or_mention(args[1], message)
            if member is None:
                return
            reason = ' '.join(args[2:])
            self.config.database.execute('INSERT INTO warns (member, reason, time, team_member) VALUES(' + str(member.id) + ', \'' + reason + '\', \'' + str(datetime.now()) + '\', ' + str(message.author.id) + ');')
            await message.channel.send(self.config.texts['moderation']['warn_success'] % (member.mention, reason, message.author.mention))
            await message.delete()
            databasecontents = self.config.database.execute('SELECT * FROM warns WHERE member = ' + str(member.id) + ' ORDER BY id;')
            active = []
            for i in databasecontents:
                date = str(datetime.now() - datetime.strptime(i[3][:19], '%Y-%m-%d %H:%M:%S'))
                if 'days' not in date:
                    active += i
                else:
                    try:
                        days = int(date.split(' ')[0])
                        if days < self.config.values['warn_expire_days']:
                            active += i
                    except ValueError:
                        pass
            if len(active) >= self.config.values['mute_warnings']:
                await self.timeout(member, self.config.values['mute_duration'], self.config.texts['moderation']['too_many_warnings'])
            if len(active) >= self.config.values['kick_warnings']:
                await self.kick(member, self.config.texts['moderation']['too_many_warnings'])
            if len(active) >= self.config.values['ban_warnings']:
                await self.ban(member, self.config.texts['moderation']['too_many_warnings'])
        elif args[0] == 'removewarn':
            try:
                warn = int(args[1])
            except ValueError:
                await message.channel.send(self.config.texts['moderation']['removewarn_failure'], delete_after=self.config.values['delete_after'])
                await message.delete(delay=self.config.values['delete_after'])
                return
            self.config.database.execute('DELETE FROM warns WHERE id = ' + str(warn) + ';')
            await message.channel.send(self.config.texts['moderation']['removewarn_success'] % warn)
            await message.delete()
        elif args[0] == 'warnings':
            if len(args) == 1:
                member = message.author
            else:
                member = await self.get_member_from_id_or_mention(args[1], message)
            if member is None:
                return
            databasecontents = self.config.database.execute('SELECT * FROM warns WHERE member = ' + str(member.id) + ' ORDER BY id;')
            result = self.config.texts['moderation']['warnings_success'] % member.mention
            if len(databasecontents) == 0:
                result += self.config.texts['moderation']['warnings_none']
            else:
                for i in databasecontents:
                    result += self.config.texts['moderation']['warnings_item'] % (self.get_readable_datetime(i[3]), i[2], self.config.get_member(i[4]).mention, i[0])
                    date = str(datetime.now() - datetime.strptime(i[3][:19], '%Y-%m-%d %H:%M:%S'))
                    if 'days' in date:
                        try:
                            days = int(date.split(' ')[0])
                            if days >= self.config.values['warn_expire_days']:
                                result += self.config.texts['moderation']['warnings_expired']
                        except ValueError:
                            pass
            await message.channel.send(result)
            print(databasecontents)
        elif args[0] == 'mute':
            # TODO
            pass
        elif args[0] == 'unmute':
            # TODO
            pass
        elif args[0] == 'kick':
            member = await self.get_non_team_member_from_id_or_mention(args[1], message)
            if member is not None:
                await self.kick(member, ' '.join(args[2:]))
        elif args[0] == 'ban':
            member = await self.get_non_team_member_from_id_or_mention(args[1], message)
            if member is not None:
                await self.ban(member, ' '.join(args[2:]))
        elif args[0] == 'unban':
            member = await self.get_member_from_id_or_mention(args[1], message)
            if member is not None:
                member.unban(' '.join(args[2:]))


class Ping(Module):
    async def on_message(self, message: discord.Message) -> None:
        if str(message.content).startswith('!ping'):
            created_at = message.created_at
            utcnow = datetime.utcnow()
            if utcnow > created_at:
                time = str(utcnow - created_at)
            else:
                time = str(created_at - utcnow)
            if time.startswith('0:00:'):
                await message.channel.send(self.config.texts['ping']['success'] % str(float(str(time)[5:])))
            else:
                await message.channel.send(self.config.texts['ping']['failure'])


class RawEcho(Module):
    async def on_message(self, message: discord.Message) -> None:
        if str(message.content).startswith('!rawecho '):
            await message.channel.send('`' + str(message.content)[len('!rawecho '):] + '`')


class Reload(Module):
    async def on_message(self, message: discord.Message) -> None:
        if str(message.content).startswith('!reload'):
            await message.channel.send(self.config.texts['reload']['start'])
            self.config.load()
            await message.channel.send(self.config.texts['reload']['end'])


class Roles(Module):
    async def on_message(self, message: discord.Message) -> None:
        content = str(message.content)
        if content.startswith('!videos'):
            await message.author.add_roles(self.config.get_video_role())
            await message.channel.send(self.config.texts['roles']['videos'])
        elif content.startswith('!keinevideos'):
            await message.author.remove_roles(self.config.get_video_role())
            await message.channel.send(self.config.texts['roles']['keinevideos'])
        elif self.config.is_team(message.author):
            if content.startswith('!chatsupport'):
                await message.author.add_roles(self.config.get_chat_support_role())
                await message.channel.send(self.config.texts['roles']['chatsupport'])
            elif content.startswith('!keinchatsupport'):
                await message.author.remove_roles(self.config.get_chat_support_role())
                await message.channel.send(self.config.texts['roles']['keinchatsupport'])
            elif content.startswith('!voicesupport'):
                await message.author.add_roles(self.config.get_voice_support_role())
                await message.channel.send(self.config.texts['roles']['voicesupport'])
            elif content.startswith('!keinvoicesupport'):
                await message.author.remove_roles(self.config.get_voice_support_role())
                await message.channel.send(self.config.texts['roles']['keinvoicesupport'])
        else:
            await message.channel.send(self.config.texts['team_only'], delete_after=self.config.values['delete_after'])


class Rules(Module):
    def __init__(self, config: Config):
        super().__init__(config)
        self.messages = 0

    @tasks.loop(seconds=1)
    async def run_schedule(self):
        if self.messages > int(self.config.values['rules_limit']):
            await self.send_message()

    async def send_message(self):
        await self.config.get_chat().send(self.config.texts['rules'] % (self.config.get_rules().mention, self.config.get_short_rules().mention))
        self.messages = 0

    async def on_message(self, message: discord.Message) -> None:
        self.messages = self.messages + 1
        if str(message.content).startswith('!regeln'):
            await self.send_message()

    async def on_ready(self) -> None:
        self.run_schedule.change_interval(seconds=self.config.delays['rules'])
        self.run_schedule.start()


class Slowmode(Module):
    def __init__(self, config: Config):
        super().__init__(config)
        self.messages = 0

    @tasks.loop(seconds=1)
    async def run_schedule(self):
        if self.messages > 15:
            await self.config.get_chat().edit(slowmode_delay=15)
        elif self.messages > 10:
            await self.config.get_chat().edit(slowmode_delay=10)
        elif self.messages > 5:
            await self.config.get_chat().edit(slowmode_delay=5)
        else:
            await self.config.get_chat().edit(slowmode_delay=0)
        self.messages = 0

    async def on_message(self, message: discord.Message) -> None:
        if message.channel.id == self.config.get_chat().id:
            self.messages = self.messages + 1

    async def on_ready(self) -> None:
        self.run_schedule.change_interval(seconds=self.config.delays['slowmode'])
        self.run_schedule.start()


class Tricks(Module):
    def __init__(self, config: Config):
        super().__init__(config)
        self.tricks = {}

    async def on_message(self, message: discord.Message) -> None:
        content = str(message.content).lower()
        if content.startswith('!'):
            if content.startswith('!addtrick'):
                if not self.config.is_team(message.author):
                    await message.channel.send(self.config.texts['team_only'], delete_after=self.config.values['delete_after'])
                    return
                split = message.content.split(' ')
                if len(split) > 2:
                    name = split[1].lower()
                    text = message.content.replace('!addtrick ' + name + ' ', '')
                    self.config.database.execute('INSERT INTO tricks (id, text) VALUES(\'' + name + '\', \'' + text + '\');')
                    self.tricks[name] = text
                    await message.channel.send((self.config.texts['tricks']['added'] % name) + text)
            elif content.startswith('!removetrick'):
                if not self.config.is_team(message.author):
                    await message.channel.send(self.config.texts['team_only'], delete_after=self.config.values['delete_after'])
                    return
                split = message.content.split(' ')
                if len(split) > 1:
                    name = split[1].lower()
                    self.config.database.execute('DELETE FROM tricks WHERE id = \'' + name + '\';')
                    self.tricks.pop(name)
                    await message.channel.send(self.config.texts['tricks']['removed'] % name)
            elif content.startswith('!tricks'):
                tricklist = ''
                for elem in self.tricks:
                    tricklist += '\n!'
                    tricklist += elem
                if len(tricklist) == 0:
                    await message.channel.send(self.config.texts['tricks']['list'] + self.config.texts['tricks']['none'])
                else:
                    await message.channel.send(self.config.texts['tricks']['list'] + tricklist)
            else:
                name = content.split(' ')[0][1:]
                if name in self.tricks:
                    await message.channel.send('**!' + name + '**\n\n' + self.tricks[name])

    async def on_ready(self) -> None:
        tricks = self.config.database.execute('SELECT id FROM tricks;')
        for elem in tricks:
            self.tricks[elem[0]] = self.config.database.execute('SELECT text FROM tricks WHERE id = \'' + elem[0] + '\';')[0][0]


class UserInfo(Module):
    async def on_message(self, message: discord.Message) -> None:
        if str(message.content).startswith('!userinfo'):
            if message.channel.id != self.config.get_bots().id:
                await message.channel.send(self.config.texts['userinfo']['wrong_channel'] % self.config.get_bots().mention, delete_after=self.config.values['delete_after'])
                await message.delete(delay=self.config.values['delete_after'])
                return
            args = str(message.content).split(' ')
            if len(message.mentions) > 1 or len(args) > 2:
                await message.channel.send(self.config.texts['userinfo']['multiple_arguments'], delete_after=self.config.values['delete_after'])
                await message.delete(delay=self.config.values['delete_after'])
                return
            elif len(args) == 1:
                member = message.author
            else:
                member = self.get_member_from_id_or_mention(args[1], message)
                if member is None:
                    return
            embed = self.embed(member.display_name).set_thumbnail(url=member.avatar_url)
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
        if after.channel is not None and after.channel.id == self.config.get_voice_support_channel().id:
            await self.config.get_team_voice_support_channel().send(self.config.texts['voice_support'] % (self.config.get_voice_support_role().mention, member.mention))
