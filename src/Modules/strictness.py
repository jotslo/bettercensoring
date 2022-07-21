from Modules import functions

async def run(message, guild_settings):
    # get arguments, stop function if none are found or user is not admin
    arguments = await functions.get_arguments("filter-strictness", message)
    if not (arguments and await functions.is_admin(message, guild_settings)):
        return
    
    # toggle embeds based on arguments, or return error if invalid
    choices = ["low", "medium", "high"]
    if arguments[0] in choices:
        strictness_choice = choices.index(arguments[0])
        functions.set_data(
            "UPDATE guild_settings SET filter_strictness = (?) WHERE guild_id = (?)",
            (strictness_choice, guild_settings["guild_id"], )
        )
        await functions.send_embed(
            message.channel,
            "<:thumbs_up:703358705089118299> Setting Updated",
            "Filter strictness has been set to **{0}**.".format(choices[strictness_choice])
            + ("\n*Note: Message replacements are temporarily disabled for high strictness.*" if strictness_choice == 2 else "")
        )
    else:
        await functions.send_error(message.channel, "Expected 'low', 'medium' or 'high'", "filter-strictness")