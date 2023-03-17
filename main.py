from modules import *

time = datetime.now()
bot = discord.Client(intents=discord.Intents.all(), allowed_mentions=discord.AllowedMentions.none())
config = Config(bot)
modules = [
    AmongUs(config),
    CapsModeration(config),
    Clear(config),
    Counter(config),
    Creeper(config),
    EmoteModeration(config),
    Flomote(config),
    Levels(config),
    LinkModeration(config),
    Logger(config),
    Moderation(config),
    Ping(config),
    RawEcho(config),
    Reload(config),
    Roles(config),
    Rules(config),
    Slowmode(config),
    Tickets(config),
    Tricks(config),
    UserInfo(config),
    VoiceSupport(config)
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
async def on_reaction_add(reaction: discord.Reaction, member: discord.Member) -> None:
    if member == bot.user or member.bot:
        return
    for module in modules:
        await module.on_reaction_add(reaction, member)


@bot.event
async def on_reaction_remove(reaction: discord.Reaction, member: discord.Member) -> None:
    if member == bot.user or member.bot:
        return
    for module in modules:
        await module.on_reaction_remove(reaction, member)


@bot.event
async def on_ready() -> None:
    print('Successfully booted up as user', bot.user)
    print('Booting took', datetime.now() - time)
    for module in modules:
        await module.on_ready()


@bot.event
async def on_voice_state_update(member: discord.Member, before: discord.VoiceState, after: discord.VoiceState) -> None:
    if member == bot.user or member.bot:
        return
    for module in modules:
        await module.on_voice_state_update(member, before, after)


bot.run(config.token)
