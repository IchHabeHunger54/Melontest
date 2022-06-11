from modules import *

time = datetime.now()
bot = discord.Client(intents=discord.Intents.all(), command_prefix='!', case_insensitive=True)
config = Config(bot)
modules = [
    Counter(config, Database(config.counter_user, config.counter_pw, config.host, config.counter_db)),
    Logger(config),
    Ping(config),
    RawEcho(config),
    Tricks(config, Database(config.tricks_user, config.tricks_pw, config.host, config.tricks_db)),
    VoiceSupportNotification(config)
]


@bot.event
async def on_member_join(member: discord.Member) -> None:
    for module in modules:
        await module.on_member_join(member)


@bot.event
async def on_member_remove(member: discord.Member) -> None:
    for module in modules:
        await module.on_member_remove(member)


@bot.event
async def on_message(message: discord.Message) -> None:
    if message.author == bot.user or message.author.bot:
        return
    for module in modules:
        await module.on_message(message)


@bot.event
async def on_message_delete(message: discord.Message) -> None:
    if message.author == bot.user or message.author.bot:
        return
    for module in modules:
        await module.on_message_delete(message)


@bot.event
async def on_message_edit(before: discord.Message, after: discord.Message) -> None:
    if before.author == bot.user or before.author.bot:
        return
    for module in modules:
        await module.on_message_edit(before, after)


@bot.event
async def on_ready() -> None:
    for module in modules:
        await module.on_ready()
    print('Successfully booted up as user', bot.user)
    print('Booting took', datetime.now() - time)


@bot.event
async def on_voice_state_update(member: discord.Member, before: discord.VoiceState, after: discord.VoiceState) -> None:
    if member == bot.user or member.bot:
        return
    for module in modules:
        await module.on_voice_state_update(member, before, after)


bot.run(config.token)
