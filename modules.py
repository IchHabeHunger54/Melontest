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
        members = self.config.get_server().members.copy()
        self.impostor = members[random.randint(0, len(members) - 1)]
        members.remove(self.impostor)
        self.crewmate1 = members[random.randint(0, len(members) - 1)]
        members.remove(self.crewmate1)
        self.crewmate2 = members[random.randint(0, len(members) - 1)]
        members.remove(self.crewmate2)
        self.order = [self.impostor, self.crewmate1, self.crewmate2]
        random.shuffle(self.order)
        self.message = await self.config.get_chat().send(self.config.texts['among_us']['start'] % (self.order[0].display_name, self.order[1].display_name, self.order[2].display_name))
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
            reaction.message.channel.send(self.config.texts['among_us']['end'] % (username, self.impostor.display_name, usernames[2:]))
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
    def __init__(self, config: Config):
        super().__init__(config)

    async def on_message(self, message: discord.Message) -> None:
        content = str(message.content).lower()
        if str(message.content).lower().startswith('!clear '):
            strings = content.split(' ')
            if len(strings) > 1 and strings[1].isnumeric():
                async for m in message.channel.history(limit=int(strings[1])):
                    await m.delete()


class Counter(Module):
    def __init__(self, config: Config):
        super().__init__(config)

    async def on_message(self, message: discord.Message) -> None:
        content = str(message.content).lower()
        variable = None
        amount = 0
        if content.endswith('='):
            variable = content.replace('=', '')
            result = self.config.database.execute('SELECT val FROM counters WHERE id = \'' + variable + '\';')
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
            old = self.config.database.execute('SELECT val FROM counters WHERE id = \'' + variable + '\';')
            if len(old) == 0:
                self.config.database.execute('REPLACE INTO counters (id, val) VALUES(\'' + variable + '\', ' + str(amount) + ');')
            else:
                amount += old[0][0]
                self.config.database.execute('UPDATE counters SET val = ' + str(amount) + ' WHERE id = \'' + variable + '\';')
            result = self.config.database.execute('SELECT val FROM counters WHERE id = \'' + variable + '\';')
            await message.channel.send(variable + ' = ' + str(result[0][0]))


class Creeper(Module):
    def __init__(self, config: Config):
        super().__init__(config)

    async def on_message(self, message: discord.Message) -> None:
        if str(message.content).startswith('!creeper') or str(message.content).startswith('creeper') or str(message.content).startswith('creper'):
            await message.channel.send(self.config.texts['creeper'])


class Flomote(Module):
    def __init__(self, config: Config):
        super().__init__(config)

    async def on_message(self, message: discord.Message) -> None:
        if str(message.content).lower().startswith('flomote'):
            await message.channel.send(self.config.texts['flomote'])
        if str(message.content).lower().startswith('floeyes'):
            await message.channel.send(self.config.texts['floeyes'])


class Logger(Module):
    def __init__(self, config: Config):
        super().__init__(config)

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


class Ping(Module):
    def __init__(self, config: Config):
        super().__init__(config)

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
    def __init__(self, config: Config):
        super().__init__(config)

    async def on_message(self, message: discord.Message) -> None:
        if str(message.content).startswith('!rawecho '):
            await message.channel.send('`' + str(message.content)[len('!rawecho '):] + '`')


class Reload(Module):
    def __init__(self, config: Config):
        super().__init__(config)

    async def on_message(self, message: discord.Message) -> None:
        if str(message.content).startswith('!reload'):
            await message.channel.send(self.config.texts['reload']['start'])
            self.config.load()
            await message.channel.send(self.config.texts['reload']['end'])


class Roles(Module):
    def __init__(self, config: Config):
        super().__init__(config)

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
        self.messages = int(self.config.values['rules_limit'])

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
                    self.config.database.execute('REPLACE INTO tricks (id, text) VALUES(\'' + name + '\', \'' + text + '\');')
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
    def __init__(self, config: Config):
        super().__init__(config)

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
                user = message.author
            else:
                if args[1].startswith('<@') and args[1].endswith('>'):
                    args[1] = args[1][2:-1]
                try:
                    userid = int(args[1])
                except ValueError:
                    await message.channel.send(self.config.texts['userinfo']['invalid_argument'], delete_after=self.config.values['delete_after'])
                    await message.delete(delay=self.config.values['delete_after'])
                    return
                user = self.config.get_member(userid)
                if user is None:
                    await message.channel.send(self.config.texts['userinfo']['unknown_user'] % str(userid), delete_after=self.config.values['delete_after'])
                    await message.delete(delay=self.config.values['delete_after'])
                    return
            embed = self.embed(user.display_name).set_thumbnail(url=user.avatar_url)
            embed.add_field(name=self.config.texts['userinfo']['user'], value=user.name + '#' + user.discriminator, inline=False)
            embed.add_field(name=self.config.texts['userinfo']['id'], value=user.id, inline=False)
            embed.add_field(name=self.config.texts['userinfo']['mention'], value=user.mention, inline=False)
            embed.add_field(name=self.config.texts['userinfo']['account_created'], value=self.get_readable_datetime(str(user.created_at)), inline=False)
            embed.add_field(name=self.config.texts['userinfo']['guild_joined'], value=self.get_readable_datetime(str(user.joined_at)), inline=False)
            premium = user.premium_since
            if premium is not None:
                embed.add_field(name=self.config.texts['userinfo']['booster_since'], value=self.get_readable_datetime(str(premium)), inline=False)
            await message.channel.send(embed=embed)


class VoiceSupport(Module):
    def __init__(self, config: Config):
        super().__init__(config)

    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState) -> None:
        if after.channel is not None and after.channel.id == self.config.get_voice_support_channel().id:
            await self.config.get_team_voice_support_channel().send(self.config.texts['voice_support'] % (self.config.get_voice_support_role().mention, member.mention))
