from Modules import data, functions

async def _set(message, guild_settings, arguments):
    # check if arguments are valid, otherwise error
    if len(arguments) >= 2:
        if arguments[1] in data.allowed_replacements:
            
            # update database and inform user
            functions.set_data(
                "UPDATE guild_settings SET replacement_char = (?) WHERE guild_id = (?)",
                ("\\" + arguments[1], guild_settings["guild_id"], )
            )
            await functions.send_embed(
                message.channel,
                "<:thumbs_up:703358705089118299> Setting Updated",
                "Replacement character is now set to **\{0}**.".format(arguments[1])
            )

        else:
            await functions.send_error(message.channel, "Invalid Replacement Character", "message-replace")
    else:
        await functions.send_error(message.channel, "Missing Arguments", "message-replace")


async def run(message, guild_settings):
    # get arguments, stop function if none are found or user is not admin
    arguments = await functions.get_arguments("message-replace", message)
    if not (arguments and await functions.is_admin(message, guild_settings)):
        return
    
    # toggle embeds based on arguments, or return error if invalid
    if arguments[0] in ["on", "off", "enable", "disable"]:
        is_enabled = int(arguments[0] in ["on", "enable"])
        functions.set_data(
            "UPDATE guild_settings SET replace_messages = (?) WHERE guild_id = (?)",
            (is_enabled, guild_settings["guild_id"], )
        )
        await functions.send_embed(
            message.channel,
            "<:thumbs_up:703358705089118299> Setting Updated",
            "Message replacing is now **{0}**.".format(["disabled", "enabled"][is_enabled])
        )
    
    # if argument is set, call set function
    elif arguments[0] == "set":
        await _set(message, guild_settings, arguments)

    # otherwise, return error
    else:
        await functions.send_error(message.channel, "Expected 'on', 'off' or 'set'", "message-replace")