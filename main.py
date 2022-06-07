from modules import *

bot = discord.Client(intents=discord.Intents.all(), command_prefix='!', case_insensitive=True)
config = Config(bot)
database = Database(config)
modules = [
    Counter(config, database),
    Logger(config, database),
    Tricks(config, database)
]


@bot.event
async def on_member_join(member: discord.Member) -> None:
    for module in modules:
        module.on_member_join(member)


@bot.event
async def on_member_remove(member: discord.Member) -> None:
    for module in modules:
        module.on_member_remove(member)


@bot.event
async def on_message(message: discord.Message) -> None:
    for module in modules:
        module.on_message(message)


@bot.event
async def on_message_delete(message: discord.Message) -> None:
    if message.author == bot.user or message.author.bot:
        return
    for module in modules:
        module.on_message_delete(message)


@bot.event
async def on_message_edit(before: discord.Message, after: discord.Message) -> None:
    if before.author == bot.user or before.author.bot:
        return
    for module in modules:
        module.on_message_edit(before, after)


@bot.event
async def on_ready() -> None:
    config.get_message_log()
    config.get_voice_log()
    config.get_join_log()
    config.get_leave_log()
    for module in modules:
        module.on_ready()


@bot.event
async def on_voice_state_update(member: discord.Member, before: discord.VoiceState, after: discord.VoiceState) -> None:
    for module in modules:
        module.on_voice_state_update(member, before, after)


bot.run(config.token)
