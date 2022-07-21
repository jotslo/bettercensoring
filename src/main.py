import discord, asyncio, aiohttp, sqlite3, confusables, json, requests, csv, time
from discord import Webhook, RequestsWebhookAdapter

intents = discord.Intents.default()
intents.members = True

client = discord.Client(intents=intents)

from Modules import *

last_status_change = time.time()
command_list = {
    "help": commands.help,
    "settings": commands.settings,
    "invite": commands.invite,
    "pro": commands.pro,
    "phrases": phrases.run,
    "links": links.run,
    "embeds": embeds.run,
    "nicknames": nicknames.run,
    "bypass": bypass.run,
    "strictness": strictness.run,
    "ignore": ignore.run,
    "replace": replace.run
}
strictness_modules = [
    low_strictness,
    med_strictness,
    high_strictness
]


async def interpret_command(message):
    # if command exists, get proper name & call associated func
    inputted_command = message.content.lower().split()[0]
    guild_settings = functions.get_settings(message.guild.id)

    for name in data.command_aliases:
        if name == inputted_command[len(data.prefix):]:
            command = data.command_aliases[name]
            await command_list[command](message, guild_settings)
            return True


async def filter_message(message, is_edit):
    guild_settings = functions.get_settings(message.guild.id)

    # skip if user doesn't need their message filtered
    if not guild_settings: return
    #if not guild_settings["phrase_blacklist"] and not guild_settings["link_blacklist"]: return
    if str(message.channel.id) in guild_settings["ignored_channels"]:
        return

    author = message.author
    if type(author) == discord.user.User:
        author = message.guild.get_member(author)

    for role in message.author.roles:
        if str(role.id) in guild_settings["ignored_roles"]:
            return
    
    # use relevant strictness to filter message
    strictness = guild_settings["filter_strictness"]
    filtered_message = await strictness_modules[strictness].filter(
        message.content,
        message.attachments,
        message.embeds,
        guild_settings,
        is_edit,
        client,
        False
    )

    # remove, repost and log message if filtered
    if filtered_message != message.content:
        try:
            await message.delete()

            # if replacement message is given, check for dodgy filtered links (https://\*\*\* etc)
            if filtered_message:
                
                user = message.author
                webhook_info = await functions.get_webhook(client.user, message.channel, await message.guild.webhooks())
                webhook = Webhook.partial(webhook_info.id, webhook_info.token, adapter=RequestsWebhookAdapter())
                webhook.send(filtered_message, username = user.nick or user.name, avatar_url = user.avatar_url)
        
        # if error, message presumably already deleted?
        except:
            0


async def filter_nickname(before, after):
    guild_settings = functions.get_settings(before.guild.id)

    # skip if user doesn't need their message filtered
    if not guild_settings: return
    if not guild_settings["phrase_blacklist"]: return
    if not guild_settings["filter_nicknames"]: return
    for role in after.roles:
        if str(role.id) in guild_settings["ignored_roles"]:
            return
    
    # get current name of user
    current_name = after.nick or after.name
    previous_name = before.nick or before.name
    
    #use relevant strictness to filter message
    strictness = guild_settings["filter_strictness"]
    filtered_name = (await strictness_modules[strictness].filter(
        current_name, [], [], guild_settings, False, client, True
    )).replace("\\", "")

    # compare nickname with original, revert or replace
    if filtered_name != current_name:
        """filtered_replacement = await strictness_modules.filter(
            "Unnamed"
        )"""
        await after.edit(nick = filtered_name)#filtered_replacement)
        """if previous_name != current_name:
            await after.edit(nick = previous_name)
        else:
            await after.edit(nick = "Unnamed")"""


@client.event
async def on_member_update(before, after):
    if after.bot: return
    await filter_nickname(before, after)


"""@client.event
async def on_raw_message_edit(payload):
    channel = client.get_channel(payload.channel_id)
    message = await channel.fetch_message(payload.message_id)

    if not message.author.bot and message.guild:
        await filter_message(message, True) # is an edit"""


@client.event
async def on_message_edit(original, message):
    if not message.author.bot and message.guild:
        await filter_message(message, original.content != message.content) # is an edit


@client.event
async def on_message(message):
    if message.author.bot or not message.guild:
        return
    
    # interpret command if starts with prefix
    if message.content.startswith(data.prefix):
        command_exists = await interpret_command(message)
        if not command_exists:
            await functions.send_embed(
                message.channel,
                "⚠️ Unknown Command",
                "That command doesn't exist. If you're unsure, type `bc:help`."
            )

    await filter_message(message, False) # not an edit


@client.event
async def on_guild_join(guild):
    global last_status_change
    
    # setup server data and send intro message to server owner
    if functions.get_data("SELECT * FROM guild_settings WHERE guild_id = (?)", (str(guild.id), )):
        await functions.send_embed(guild.owner, "BetterCensoring", data.welcome_message) # TEMP
    else:
        functions.set_data("INSERT INTO guild_settings (guild_id) VALUES (?)", (str(guild.id), ))
        await functions.send_embed(guild.owner, "BetterCensoring", data.welcome_message)

    # display bot presence in new servers after 60 sec cooldown
    current_time = time.time()
    if current_time - last_status_change >= 60:
        await client.change_presence(activity = discord.Game(name = data.rich_presence))
        last_status_change = current_time


@client.event
async def on_guild_remove(guild):
    # if still possible, send final goodbye message to server owner
    try:
        await functions.send_embed(guild.owner, "BetterCensoring", data.leave_message)
    
    except:
        "otherwise, do nothing"


@client.event
async def on_ready():
    await client.change_presence(activity = discord.Game(name = data.rich_presence))


# determine which bot token to use & start bot
if data.bot_type == "A": # alpha
    client.run(data.alpha_token)
elif data.bot_type == "B": # beta
    client.run(data.beta_token)
elif data.bot_type == "R": # release
    client.run(data.token)