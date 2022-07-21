import discord, json
from Modules import functions, data


async def help(message, guild_settings):
    await functions.send_embed(message.channel, "Help", data.description + data.help_message + data.vote_message)


async def invite(message, guild_settings):
    await functions.send_embed(
        message.channel,
        "Invite",
        "**[Click here](https://discord.com/oauth2/authorize?client_id=678993339873493022&scope=bot&permissions=738585616&response_type=code&redirect_uri=https%3A%2F%2Fdiscord.gg%2FZmTSqzt)** to invite me to your server."
    )


async def pro(message, guild_settings):
    await functions.send_embed(message.channel, "BetterCensoring Pro", data.pro_message)


async def settings(message, guild_settings):
    # ignore request if user doesn't have perms
    if not await functions.is_admin(message, guild_settings):
        return
    
    # handle deprecated bot usage
    arguments = message.content.split()
    if len(arguments) > 1:
        if arguments[1] in data.deprecated_cmds:
            await functions.send_error(message.channel, "Deprecated Command", "")
            return
    
    # setup settings display
    settings_message = data.settings_list.format(
        len(guild_settings["phrase_blacklist"]),
        len(guild_settings["phrase_whitelist"]),
        ["<:thumbs_down:703358705067884655>", "<:thumbs_up:703358705089118299>"][guild_settings["replace_messages"]],
        ["<:thumbs_down:703358705067884655>", "<:thumbs_up:703358705089118299>"][guild_settings["link_whitelist_enabled"]],
        len(guild_settings["link_whitelist"]),
        len(guild_settings["link_blacklist"]),
        ["<:thumbs_down:703358705067884655>", "<:thumbs_up:703358705089118299>"][guild_settings["allow_invites"]],
        ["<:thumbs_down:703358705067884655>", "<:thumbs_up:703358705089118299>"][guild_settings["filter_embeds"]],
        ["<:thumbs_down:703358705067884655>", "<:thumbs_up:703358705089118299>"][guild_settings["filter_nicknames"]],
        ["<:thumbs_down:703358705067884655>", "<:thumbs_up:703358705089118299>"][guild_settings["allow_unicode"]],
        ["Low", "Medium", "High"][guild_settings["filter_strictness"]],
        ["<:thumbs_down:703358705067884655>", "<:thumbs_up:703358705089118299>"][guild_settings["bypass_detection"]],
        len(guild_settings["ignored_roles"] + guild_settings["ignored_channels"]),
        guild_settings["mute_requirement"],
        guild_settings["kick_requirement"],
        guild_settings["ban_requirement"],
        ["<:thumbs_down:703358705067884655>", "<:thumbs_up:703358705089118299>"][guild_settings["filter_images"]],
        ["<:thumbs_down:703358705067884655>", "<:thumbs_up:703358705089118299>"][guild_settings["filter_webpages"]],
        ["<:thumbs_down:703358705067884655>", "<:thumbs_up:703358705089118299>"][guild_settings["extension_whitelist_enabled"]],
        len(guild_settings["extension_blacklist"]),
        len(guild_settings["extension_whitelist"]),
        ["<:thumbs_down:703358705067884655>", "<:thumbs_up:703358705089118299>"][guild_settings["filter_files"]]
    )

    # remove lock emoji if necessary, and output
    if guild_settings["is_pro"]:
        settings_message = settings_message.replace("🔒 ", "")
    else:
        #settings_message += "\n**To access locked features, learn more [here](https://censoring.io/pro).**"
        settings_message += "\n**More features coming soon.**"

    await functions.send_embed(message.channel, "Settings", settings_message)

