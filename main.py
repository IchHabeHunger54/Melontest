from modules import *

time = datetime.now()
bot = Client(intents=Intents.all(), allowed_mentions=AllowedMentions.none())
config = Config(bot)
config.modules = [
    AmongUs(config, 'among_us'),
    CapsModeration(config, 'caps_moderation'),
    Clear(config, 'clear'),
    Counter(config, 'counter'),
    Creeper(config, 'creeper'),
    DefaultRole(config, 'default_role'),
    EmbedOnlyChannel(config, 'embed_only'),
    EmoteModeration(config, 'emote_moderation'),
    Flomote(config, 'flomote'),
    Help(config, 'help'),
    Levels(config, 'levels'),
    Logger(config, 'logger'),
    Moderation(config, 'moderation'),
    Ping(config, 'ping'),
    PrankMute(config, 'prank_mute'),
    RawEcho(config, 'raw_echo'),
    Reload(config, 'reload'),
    RockPaperScissors(config, 'rps'),
    Roles(config, 'roles'),
    Rules(config, 'rules'),
    SelfDestruct(config, 'self_destruct'),
    Slowmode(config, 'slowmode'),
    TempVoice(config, 'temp_voice'),
    Tickets(config, 'tickets'),
    Tricks(config, 'tricks'),
    Userinfo(config, 'userinfo'),
    VoiceSupport(config, 'voice_support'),
    Write(config, 'write')
]
config.load()


@bot.event
async def on_member_join(member: Member) -> None:
    for m in config.modules:
        await m.on_member_join(member)


@bot.event
async def on_member_remove(member: Member) -> None:
    for m in config.modules:
        await m.on_member_remove(member)


@bot.event
async def on_member_update(before: Member, after: Member) -> None:
    if before is None or after is None:
        return
    for m in config.modules:
        await m.on_member_update(before, after)


@bot.event
async def on_user_update(before: User, after: User) -> None:
    if before is None or after is None:
        return
    for m in config.modules:
        await m.on_user_update(before, after)


@bot.event
async def on_message(message: Message) -> None:
    if message.author == bot.user or message.author.bot:
        return
    if message.content == '':
        return
    for m in config.modules:
        await m.on_message(message)


@bot.event
async def on_message_delete(message: Message) -> None:
    if message.author == bot.user or message.author.bot:
        return
    if message.content == '':
        return
    for m in config.modules:
        await m.on_message_delete(message)


@bot.event
async def on_message_edit(before: Message, after: Message) -> None:
    if before.author == bot.user or before.author.bot:
        return
    if before.content == '' and after.content == '':
        return
    for m in config.modules:
        await m.on_message_edit(before, after)


@bot.event
async def on_reaction_add(reaction: Reaction, member: Member) -> None:
    if member == bot.user or member.bot:
        return
    for m in config.modules:
        await m.on_reaction_add(reaction, member)


@bot.event
async def on_reaction_remove(reaction: Reaction, member: Member) -> None:
    if member == bot.user or member.bot:
        return
    for m in config.modules:
        await m.on_reaction_remove(reaction, member)


@bot.event
async def on_ready() -> None:
    for m in config.modules:
        await m.on_ready()
    print('Successfully booted up as user', bot.user)
    print('Booting took', datetime.now() - time)


@bot.event
async def on_voice_state_update(member: Member, before: VoiceState, after: VoiceState) -> None:
    if member is None or member == bot.user or member.bot:
        return
    for m in config.modules:
        await m.on_voice_state_update(member, before, after)


bot.run(config.token)
