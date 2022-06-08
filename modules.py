import discord

from config import Config
from database import Database
from module import Module


class Counter(Module):
    def __init__(self, config: Config, database: Database):
        super().__init__(config, database)

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


class Logger(Module):
    def __init__(self, config: Config, database: Database):
        super().__init__(config, database)

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
        embed.add_field(name='User:', value=before.author.mention, inline=False)
        embed.add_field(name='Channel:', value=before.channel.mention, inline=False)
        embed.add_field(name='Vorher:', value=before.content, inline=False)
        embed.add_field(name='Nachher:', value=after.content, inline=True)
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


class Tricks(Module):
    def __init__(self, config: Config, database: Database):
        super().__init__(config, database)
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
