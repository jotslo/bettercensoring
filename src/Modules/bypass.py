from Modules import functions

async def run(message, guild_settings):
    # get arguments, stop function if none are found or user is not admin
    arguments = await functions.get_arguments("bypass-detect", message)
    if not (arguments and await functions.is_admin(message, guild_settings)):
        return
    
    # toggle embeds based on arguments, or return error if invalid
    if arguments[0] in ["on", "off", "enable", "disable"]:
        is_enabled = int(arguments[0] in ["on", "enable"])
        functions.set_data(
            "UPDATE guild_settings SET bypass_detection = (?) WHERE guild_id = (?)",
            (is_enabled, guild_settings["guild_id"], )
        )
        await functions.send_embed(
            message.channel,
            "<:thumbs_up:703358705089118299> Setting Updated",
            "Bypass detection is now **{0}**.".format(["disabled", "enabled"][is_enabled])
        )
    else:
        await functions.send_error(message.channel, "Expected 'on' or 'off'", "bypass-detect")