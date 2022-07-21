from Modules import functions


async def _unicode(message, guild_settings, arguments):
    # check if arguments are valid, otherwise error
    if len(arguments) >= 2:
        if arguments[1] in ["allow", "block"]:
            
            # update database and inform user
            is_allowed = int(arguments[1] == "allow")
            functions.set_data(
                "UPDATE guild_settings SET allow_unicode = (?) WHERE guild_id = (?)",
                (is_allowed, guild_settings["guild_id"], )
            )
            await functions.send_embed(
                message.channel,
                "<:thumbs_up:703358705089118299> Setting Updated",
                "Unicode in nicknames is now **{0}**.".format(["blocked", "allowed"][is_allowed])
            )

        else:
            await functions.send_error(message.channel, "Expected 'allow' or 'block'", "manage-nicks")
    else:
        await functions.send_error(message.channel, "Missing Arguments", "manage-nicks")


async def run(message, guild_settings):
    # get arguments, stop function if none are found or user is not admin
    arguments = await functions.get_arguments("manage-nicks", message)
    if not (arguments and await functions.is_admin(message, guild_settings)):
        return
    
    # toggle embeds based on arguments, or return error if invalid
    if arguments[0] in ["on", "off", "enable", "disable"]:
        is_enabled = int(arguments[0] in ["on", "enable"])
        functions.set_data(
            "UPDATE guild_settings SET filter_nicknames = (?) WHERE guild_id = (?)",
            (is_enabled, guild_settings["guild_id"], )
        )
        await functions.send_embed(
            message.channel,
            "<:thumbs_up:703358705089118299> Setting Updated",
            "Nickname filtering is now **{0}**.".format(["disabled", "enabled"][is_enabled])
        )
    
    # if argument is unicode, call functions, otherwise error 
    elif arguments[0] == "unicode":
        await _unicode(message, guild_settings, arguments)
    else:
        await functions.send_error(message.channel, "Unknown Command", "manage-nicks")