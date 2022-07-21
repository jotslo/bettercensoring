import json
from Modules import functions, data


async def add(message, guild_settings, arguments, request_type):
    # check for phrases in message and determine the phrase limit
    new_phrases = await functions.get_phrases(" ".join(arguments[1:]), message.attachments)

    if new_phrases:
        phrase_limit = 20000 if guild_settings["is_pro"] else 2000
        new_list = list(set(guild_settings["phrase_{0}".format(request_type.lower())] + new_phrases))
        new_list.sort()

        # if within phrase limit, add to db, otherwise show an error
        if len(", ".join(new_list)) <= phrase_limit:
            functions.set_data(
                "UPDATE guild_settings SET phrase_{0} = (?) WHERE guild_id = (?)".format(request_type.lower()),
                (json.dumps(new_list), guild_settings["guild_id"], )
            )
            await functions.send_embed(
                message.channel,
                "<:thumbs_up:703358705089118299> Phrase {0} Updated".format(request_type),
                "Successfully added **{0}** new phrase{1} to your {2}.".format(
                    len(new_phrases),
                    "s" * (len(new_phrases) != 1),
                    request_type.lower()
                )
            )
        else:
            await functions.send_embed(
                 message.channel,
                 "⚠️ Phrase Limit Reached",
                 data.phrase_limit[guild_settings["is_pro"]]
             )

    else:
        await functions.send_error(message.channel, "No Phrases Found", "manage-phrases")


async def remove(message, guild_settings, arguments, request_type):
    # check for phrases in message
    new_phrases = await functions.get_phrases(" ".join(arguments[1:]), message.attachments)

    if new_phrases:
        new_list = functions.remove_from_list(
            guild_settings["phrase_{0}".format(request_type.lower())],
            new_phrases
        )

        # if within phrase limit, add to db, otherwise show an error
        functions.set_data(
            "UPDATE guild_settings SET phrase_{0} = (?) WHERE guild_id = (?)".format(request_type.lower()),
            (json.dumps(new_list), guild_settings["guild_id"], )
        )
        await functions.send_embed(
            message.channel,
            "<:thumbs_up:703358705089118299> Phrase {0} Updated".format(request_type),
            "Successfully removed **{0}** phrase{1} from your {2}.".format(
                len(new_phrases),
                "s" * (len(new_phrases) != 1),
                request_type.lower()
            )
        )

    else:
        await functions.send_error(message.channel, "No Phrases Found", "manage-phrases")


async def view(message, guild_settings, arguments, request_type):
    string_list = guild_settings["phrase_{0}".format(request_type.lower())]

    # if there are words in white/blacklist, return contents
    if string_list:
        separator = [", ", ","][len(", ".join(string_list)) > 1800]
        await functions.send_embed(
            message.channel,
            "Phrase {0}".format(request_type),
            "`" + separator.join(string_list) + """`

To learn how to modify to your filter, click **[here](https://censoring.io/commands#manage-phrases)**."""
        )

    # otherwise, return error
    else:
        await functions.send_error(
            message.channel,
            "Phrase {0} Empty".format(request_type),
            "manage-phrases"
        )


async def blacklist(message, guild_settings, arguments):
    # if arguments given, allow users to add to blacklist
    if len(arguments) > 1:
        if arguments[1] == "add": await add(message, guild_settings, arguments[1:], "Blacklist")
        elif arguments[1] == "remove": await remove(message, guild_settings, arguments[1:], "Blacklist")
        elif arguments[1] in ["view", "list"]: await view(message, guild_settings, arguments[1:], "Blacklist")
        else: await functions.send_error(message.channel, "Unknown Command", "manage-phrases")
        
    #otherwise, show error
    else:
        await functions.send_error(message.channel, "Missing Arguments", "manage-phrases")


async def whitelist(message, guild_settings, arguments):
    # if arguments given, allow users to add to whitelist
    if len(arguments) > 1:
        if arguments[1] == "add": await add(message, guild_settings, arguments[1:], "Whitelist")
        elif arguments[1] == "remove": await remove(message, guild_settings, arguments[1:], "Whitelist")
        elif arguments[1] in ["view", "list"]: await view(message, guild_settings, arguments[1:], "Whitelist")
        else: await functions.send_error(message.channel, "Unknown Command", "manage-phrases")
    
    #otherwise, show error
    else:
        await functions.send_error(message.channel, "Missing Arguments", "manage-phrases")


# allow for "bc:phrase add" shortcut
async def bl_add(a,b,c):await add(a,b,c, "Blacklist")
async def bl_remove(a,b,c):await remove(a,b,c, "Blacklist")
async def bl_view(a,b,c):await view(a,b,c, "Blacklist")


command_list = {
    "add": bl_add,
    "remove": bl_remove,
    "view": bl_view,
    "list": bl_view,
    "blacklist": blacklist,
    "whitelist": whitelist
}


async def run(message, guild_settings):
    # get arguments, stop function if none are found or user is not admin
    arguments = await functions.get_arguments("manage-phrases", message)
    if not (arguments and await functions.is_admin(message, guild_settings)):
        return
    
    # if command exists, run associated function
    if arguments[0] in command_list.keys():
        await command_list[arguments[0]](
            message,
            guild_settings,
            arguments
        )
    else:
        await functions.send_error(message.channel, "Unknown Command", "manage-phrases")
