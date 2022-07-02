import random
from datetime import datetime

import discord
from discord.ext import tasks

from config import Config
from database import Database
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

    @tasks.loop(seconds=86400)
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
        self.message = await self.config.get_chat().send('**Ein Impostor ist unter uns!**\n\nVote einen der **drei Crewmates** raus! ' + self.config.among_us_1_emote + '\nWenn du den **Impostor** votest, erhältst du **500 Melons** fürs Levelsystem. ' + self.config.among_us_2_emote + '\nDie **überlebenden Crewmates** erhalten jeweils **100 Melons**! Bei einem **Unentschieden** bekommt jeder **100 Melons**. ' + self.config.among_us_3_emote + '\nBeeilt euch, die Abstimmung ist auf **5 Personen** begrenzt! ' + self.config.among_us_4_emote + '\n\n**1. Verdächtiger:** ' + self.order[0].display_name + '\n**2. Verdächtiger:** ' + self.order[1].display_name + '\n**3. Verdächtiger:** ' + self.order[2].display_name)
        await self.message.add_reaction('1️⃣')
        await self.message.add_reaction('2️⃣')
        await self.message.add_reaction('3️⃣')
        self.run_schedule.change_interval(seconds=self.config.among_us_delay + 2 * random.randint(0, self.config.among_us_delay_offset) - self.config.among_us_delay_offset)

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
        if len(self.reactions) == 5:
            index = None
            if self.votes[0] > self.votes[1] and self.votes[0] > self.votes[2]:
                index = self.votes[0]
            if self.votes[1] > self.votes[0] and self.votes[1] > self.votes[2]:
                index = self.votes[1]
            if self.votes[2] > self.votes[0] and self.votes[2] > self.votes[1]:
                index = self.votes[2]
            if index is None:
                username = '_niemand_'
            else:
                username = self.order[index].display_name
            users = []
            usernames = ''
            for key, value in self.reactions:
                if value == index:
                    users.append(key)
                    usernames += ', ' + self.config.get_member(key).display_name
            reaction.message.channel.send('**Gewählter Impostor:** ' + username + '\n**Richtiger Impostor:** ' + self.impostor.display_name + '\n**Richtigen Impostor gewählt:**' + usernames[2:])
            # TODO level system
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
        self.run_schedule.change_interval(seconds=self.config.among_us_delay + 2 * random.randint(0, self.config.among_us_delay_offset) - self.config.among_us_delay_offset)
        self.run_schedule.start()


class Counter(Module):
    def __init__(self, config: Config, database: Database):
        super().__init__(config)
        self.database = database

    async def on_message(self, message: discord.Message) -> None:
        content = str(message.content).lower()
        var = None
        amount = 0
        if content.endswith('='):
            var = content.replace('=', '')
            result = self.database.execute('SELECT val FROM counters WHERE id = \'' + var + '\';')
            await message.channel.send(embed=self.embed(var + ' = ' + str(result[0][0])))
        elif content.endswith('++') and content.count('++') == 1:
            var = content.replace('++', '')
            amount = 1
        elif content.endswith('--') and content.count('--') == 1:
            var = content.replace('--', '')
            amount = -1
        elif content.find('+=') and content.count('+=') == 1:
            strings = content.split('+=')
            if len(strings) == 2 and strings[1].isnumeric():
                var = strings[0]
                amount = int(strings[1])
        elif content.find('-=') and content.count('-=') == 1:
            strings = content.split('-=')
            if len(strings) == 2 and strings[1].isnumeric():
                var = strings[0]
                amount = -int(strings[1])
        if var is not None and amount != 0:
            old = self.database.execute('SELECT val FROM counters WHERE id = \'' + var + '\';')
            if len(old) == 0:
                self.database.execute('REPLACE INTO counters (id, val) VALUES(\'' + var + '\', ' + str(amount) + ');')
            else:
                amount += old[0][0]
                self.database.execute('UPDATE counters SET val = ' + str(amount) + ' WHERE id = \'' + var + '\';')
            result = self.database.execute('SELECT val FROM counters WHERE id = \'' + var + '\';')
            await message.channel.send(embed=self.embed(var + ' = ' + str(result[0][0])))


class Creeper(Module):
    def __init__(self, config: Config):
        super().__init__(config)

    async def on_message(self, message: discord.Message) -> None:
        if str(message.content).startswith('!creeper') or str(message.content).startswith('creeper') or str(message.content).startswith('creper'):
            await message.channel.send('Es ist erlaubt, das Wort Creeper zu schreiben. Es ist jedoch verboten, den Songtext von "Creeper, Aw Man" (Revenge) zu schreiben, da es in der Vergangenheit immer wieder zu Spam geführt hat.')


class Flomote(Module):
    def __init__(self, config: Config):
        super().__init__(config)

    async def on_message(self, message: discord.Message) -> None:
        if str(message.content).startswith('flomote'):
            await message.channel.send(self.config.flo_1_emote + self.config.flo_2_emote + '\n' + self.config.flo_3_emote)
        if str(message.content).startswith('floeyes'):
            await message.channel.send(self.config.flo_1_emote + self.config.flo_2_emote)


class Logger(Module):
    def __init__(self, config: Config):
        super().__init__(config)

    async def on_member_join(self, member: discord.Member) -> None:
        embed = self.embed('Server betreten')
        embed.add_field(name='User:', value=member.mention, inline=False)
        embed.add_field(name='Account erstellt:', value=member.created_at, inline=True)
        await self.config.get_join_log().send(embed=embed)

    async def on_member_remove(self, member: discord.Member) -> None:
        embed = self.error_embed(title='Server verlassen')
        embed.add_field(name='User:', value=member.mention, inline=False)
        embed.add_field(name='Account erstellt:', value=member.created_at, inline=False)
        embed.add_field(name='Server betreten:', value=member.joined_at, inline=True)
        await self.config.get_leave_log().send(embed=embed)

    async def on_message_edit(self, before: discord.Message, after: discord.Message) -> None:
        embed = self.embed('Nachricht bearbeitet')
        old = str(before.content)
        new = str(after.content)
        if old != new:
            embed.add_field(name='User:', value=before.author.mention, inline=False)
            embed.add_field(name='Channel:', value=before.channel.mention, inline=False)
            embed.add_field(name='Vorher:', value=old, inline=False)
            embed.add_field(name='Nachher:', value=new, inline=True)
            await self.config.get_message_log().send(embed=embed)

    async def on_message_delete(self, message: discord.Message) -> None:
        embed = self.error_embed('Nachricht gelöscht')
        embed.add_field(name='User:', value=message.author.mention, inline=False)
        embed.add_field(name='Channel:', value=message.channel.mention, inline=False)
        embed.add_field(name='Nachricht:', value=message.content, inline=True)
        await self.config.get_message_log().send(embed=embed)

    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState) -> None:
        if before.channel is not None and after.channel is not None:
            embed = self.embed('Voicechannel gewechselt')
            embed.add_field(name='User:', value=member.mention, inline=False)
            embed.add_field(name='Vorher:', value=before.channel.name, inline=False)
            embed.add_field(name='Nachher:', value=after.channel.name, inline=True)
            await self.config.get_voice_log().send(embed=embed)
        elif before.channel is None and after.channel is not None:
            embed = self.embed('Voicechannel betreten')
            embed.add_field(name='User:', value=member.mention, inline=False)
            embed.add_field(name='Channel:', value=after.channel.name, inline=True)
            await self.config.get_voice_log().send(embed=embed)
        elif before.channel is not None and after.channel is None:
            embed = self.error_embed('Voicechannel verlassen')
            embed.add_field(name='User:', value=member.mention, inline=False)
            embed.add_field(name='Channel:', value=before.channel.name, inline=True)
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
                await message.channel.send('Ping: ' + str(float(str(time)[5:])) + ' Sekunden')
            else:
                await message.channel.send('Ping: > 1 Minute. Bitte ans Team melden!')


class RawEcho(Module):
    def __init__(self, config: Config):
        super().__init__(config)

    async def on_message(self, message: discord.Message) -> None:
        if str(message.content).startswith('!rawecho '):
            await message.channel.send('`' + str(message.content)[len('!rawecho '):] + '`')


class Rules(Module):
    def __init__(self, config: Config):
        super().__init__(config)
        self.messages = 10

    @tasks.loop(seconds=3600)
    async def run_schedule(self):
        if self.messages > 10:
            await self.send_message()

    async def send_message(self):
        await self.config.get_chat().send('Bitte lest euch die Regeln in ' + self.config.get_rules().mention + ' bzw. die Kurzfassung in ' + self.config.get_short_rules().mention + ' durch!')
        self.messages = 0

    async def on_message(self, message: discord.Message) -> None:
        self.messages = self.messages + 1
        if str(message.content).startswith('!regeln'):
            await self.send_message()

    async def on_ready(self) -> None:
        self.run_schedule.start()


class Slowmode(Module):
    def __init__(self, config: Config):
        super().__init__(config)
        self.messages = 0

    @tasks.loop(seconds=60)
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
        self.run_schedule.start()


class Tricks(Module):
    def __init__(self, config: Config, database: Database):
        super().__init__(config)
        self.database = database
        self.tricks = {}

    async def on_message(self, message: discord.Message) -> None:
        content = str(message.content).lower()
        if content.startswith('!'):
            if content.startswith('!addtrick'):
                if not self.config.is_team(message.author):
                    embed = self.embed('Du hast nicht die notwendigen Berechtigungen für diesen Befehl!')
                    await message.channel.send(embed=embed)
                    return
                split = message.content.split(' ')
                if len(split) > 2:
                    name = split[1].lower()
                    text = message.content.replace('!addtrick ' + name + ' ', '')
                    self.database.execute('REPLACE INTO tricks (command, text) VALUES(\'' + name + '\', \'' + text + '\');')
                    self.tricks[name] = text
                    embed = self.embed('Trick !' + name + ' wurde hinzugefügt.')
                    embed.add_field(name='!' + name, value=text, inline=True)
                    await message.channel.send(embed=embed)
            elif content.startswith('!removetrick'):
                if not self.config.is_team(message.author):
                    embed = self.embed('Du hast nicht die notwendigen Berechtigungen für diesen Befehl!')
                    await message.channel.send(embed=embed)
                    return
                split = message.content.split(' ')
                if len(split) > 1:
                    name = split[1].lower()
                    self.database.execute('DELETE FROM tricks WHERE command = \'' + name + '\';')
                    self.tricks.pop(name)
                    embed = self.error_embed('Trick !' + name + ' wurde entfernt.')
                    await message.channel.send(embed=embed)
            elif content.startswith('!tricks'):
                tricklist = ''
                for elem in self.tricks:
                    tricklist += '\n!'
                    tricklist += elem
                embed = self.embed('')
                if len(tricklist) == 0:
                    embed.add_field(name='Liste aller Trickbefehle:', value='Aktuell sind keine Trickbefehle registriert.', inline=True)
                else:
                    embed.add_field(name='Liste aller Trickbefehle:', value=tricklist, inline=True)
                await message.channel.send(embed=embed)
            else:
                name = content.split(' ')[0][1:]
                if name in self.tricks:
                    embed = self.embed('')
                    embed.add_field(name='!' + name, value=self.tricks[name], inline=True)
                    await message.channel.send(embed=embed)

    async def on_ready(self) -> None:
        tricks = self.database.execute('SELECT command FROM tricks;')
        for elem in tricks:
            self.tricks[elem[0]] = self.database.execute('SELECT text FROM tricks WHERE command = \'' + elem[0] + '\';')[0][0]


class UserInfo(Module):
    def __init__(self, config: Config):
        super().__init__(config)

    async def on_message(self, message: discord.Message) -> None:
        if str(message.content).startswith('!userinfo'):
            if message.channel.id != self.config.get_bot_channel().id:
                await message.channel.send('Bitte benutze `!userinfo` nur in ' + self.config.get_bot_channel().mention + '!', delete_after=10)
                await message.delete(delay=10)
                return
            args = str(message.content).split(' ')
            if len(message.mentions) > 1 or len(args) > 2:
                await message.channel.send('`!userinfo` funktioniert nur für einen User gleichzeitig!')
                return
            elif len(args) == 1:
                user = message.author
            else:
                if args[1].startswith('<@') and args[1].endswith('>'):
                    args[1] = args[1][2:-1]
                try:
                    userid = int(args[1])
                except ValueError:
                    await message.channel.send('`!userinfo` benötigt entweder einen Ping, eine User-ID oder überhaupt kein zusätzliches Argument!')
                    return
                user = self.config.get_server().get_member(userid)
                if user is None:
                    await message.channel.send('User `' + str(userid) + '` konnte nicht gefunden werden!')
                    return
            embed = self.embed(user.display_name).set_thumbnail(url=user.avatar_url)
            embed.add_field(name='Benutzername:', value=user.name + '#' + user.discriminator, inline=False)
            embed.add_field(name='ID:', value=user.id, inline=False)
            embed.add_field(name='Ping:', value=user.mention, inline=False)
            embed.add_field(name='Account erstellt:', value=self.get_readable_datetime(str(user.created_at)), inline=False)
            embed.add_field(name='Dem Server beigetreten:', value=self.get_readable_datetime(str(user.joined_at)), inline=False)
            premium = user.premium_since
            if premium is not None:
                embed.add_field(name='Booster seit:', value=self.get_readable_datetime(str(premium)), inline=False)
            await message.channel.send(embed=embed)


class VoiceSupportNotification(Module):
    def __init__(self, config: Config):
        super().__init__(config)

    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState) -> None:
        if after.channel is not None and after.channel.id == self.config.get_voice_support_channel().id:
            await self.config.get_team_voice_support_channel().send(self.config.get_voice_support_role().mention + ' Benachrichtigung! ' + member.mention + ' benötigt Support per Voice!')
