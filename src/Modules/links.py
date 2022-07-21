import json
from Modules import functions, data


async def add(message, guild_settings, arguments, request_type):
    # check for links in message and determine the link limit
    new_links = await functions.get_links(" ".join(arguments[1:]), message.attachments)

    if new_links:
        link_limit = 20000 if guild_settings["is_pro"] else 2000
        new_list = list(set(guild_settings["link_{0}".format(request_type.lower())] + new_links))
        new_list.sort()

        # if within link limit, add to db, otherwise show an error
        if len(", ".join(new_list)) <= link_limit:
            functions.set_data(
                "UPDATE guild_settings SET link_{0} = (?) WHERE guild_id = (?)".format(request_type.lower()),
                (json.dumps(new_list), guild_settings["guild_id"], )
            )
            await functions.send_embed(
                message.channel,
                "<:thumbs_up:703358705089118299> Link {0} Updated".format(request_type),
                "Successfully added **{0}** new link{1} to your {2}.".format(
                    len(new_links),
                    "s" * (len(new_links) != 1),
                    request_type.lower()
                )
            )
        else:
            await functions.send_embed(
                 message.channel,
                 "⚠️ Link Limit Reached",
                 data.link_limit[guild_settings["is_pro"]]
             )

    else:
        await functions.send_error(message.channel, "No Links Found", "manage-links")


async def remove(message, guild_settings, arguments, request_type):
    # check for links in message
    new_links = await functions.get_links(" ".join(arguments[1:]), message.attachments)

    if new_links:
        new_list = functions.remove_from_list(
            guild_settings["link_{0}".format(request_type.lower())],
            new_links
        )

        # if within link limit, add to db, otherwise show an error
        functions.set_data(
            "UPDATE guild_settings SET link_{0} = (?) WHERE guild_id = (?)".format(request_type.lower()),
            (json.dumps(new_list), guild_settings["guild_id"], )
        )
        await functions.send_embed(
            message.channel,
            "<:thumbs_up:703358705089118299> Link {0} Updated".format(request_type),
            "Successfully removed **{0}** link{1} from your {2}.".format(
                len(new_links),
                "s" * (len(new_links) != 1),
                request_type.lower()
            )
        )

    else:
        await functions.send_error(message.channel, "No Links Found", "manage-links")


async def view(message, guild_settings, arguments, request_type):
    string_list = guild_settings["link_{0}".format(request_type.lower())]

    # if there are words in white/blacklist, return contents
    if string_list:
        separator = [", ", ","][len(", ".join(string_list)) > 1800]
        await functions.send_embed(
            message.channel,
            "Link {0}".format(request_type),
            "`" + separator.join(string_list) + """`

To learn how to modify to your filter, click **[here](https://censoring.io/commands#manage-links)**."""
        )

    # otherwise, return error
    else:
        await functions.send_error(
            message.channel,
            "Link {0} Empty".format(request_type),
            "manage-links"
        )


async def toggle(message, guild_settings, arguments):
    # update setting accordingly and send response message
    is_enabled = int(arguments[0] in ["on", "enable"])
    functions.set_data(
        "UPDATE guild_settings SET link_whitelist_enabled = (?) WHERE guild_id = (?)",
        (is_enabled, guild_settings["guild_id"], )
    )
    await functions.send_embed(
        message.channel,
        "<:thumbs_up:703358705089118299> Setting Updated",
        "Link whitelisting is now **{0}**.".format(["disabled", "enabled"][is_enabled])
    )


async def blacklist(message, guild_settings, arguments):
    # if arguments given, allow users to add to whitelist
    if len(arguments) > 1:
        if arguments[1] == "add": await add(message, guild_settings, arguments[1:], "Blacklist")
        elif arguments[1] == "remove": await remove(message, guild_settings, arguments[1:], "Blacklist")
        elif arguments[1] in ["view", "list"]: await view(message, guild_settings, arguments[1:], "Blacklist")
        else: await functions.send_error(message.channel, "Unknown Command", "manage-links")
    
    #otherwise, show error
    else:
        await functions.send_error(message.channel, "Missing Arguments", "manage-phrases")


async def whitelist(message, guild_settings, arguments):
    # if arguments given, allow users to add to whitelist
    if len(arguments) > 1:
        if arguments[1] == "add": await add(message, guild_settings, arguments[1:], "Whitelist")
        elif arguments[1] == "remove": await remove(message, guild_settings, arguments[1:], "Whitelist")
        elif arguments[1] in ["view", "list"]: await view(message, guild_settings, arguments[1:], "Whitelist")
        elif arguments[1] in ["on", "off", "enable", "disable"]: await toggle(message, guild_settings, arguments[1:])
        else: await functions.send_error(message.channel, "Unknown Command", "manage-links")
    
    #otherwise, show error
    else:
        await functions.send_error(message.channel, "Missing Arguments", "manage-phrases")


async def discord(message, guild_settings, arguments):
    # check if arguments are valid, otherwise error
    if len(arguments) >= 2:
        if arguments[1] in ["allow", "block"]:
            
            # update database and inform user
            is_allowed = int(arguments[1] == "allow")
            functions.set_data(
                "UPDATE guild_settings SET allow_invites = (?) WHERE guild_id = (?)",
                (is_allowed, guild_settings["guild_id"], )
            )
            await functions.send_embed(
                message.channel,
                "<:thumbs_up:703358705089118299> Setting Updated",
                "Discord invites are now **{0}**.".format(["blocked", "allowed"][is_allowed])
            )

        else:
            await functions.send_error(message.channel, "Expected 'allow' or 'block'", "manage-links")
    else:
        await functions.send_error(message.channel, "Missing Arguments", "manage-links")


# allow for "bc:link add" shortcut
async def bl_add(a,b,c):await add(a,b,c, "Blacklist")
async def bl_remove(a,b,c):await remove(a,b,c, "Blacklist")
async def bl_view(a,b,c):await view(a,b,c, "Blacklist")


command_list = {
    "add": bl_add,
    "remove": bl_remove,
    "view": bl_view,
    "list": bl_view,
    "blacklist": blacklist,
    "whitelist": whitelist,
    "discord": discord
}


async def run(message, guild_settings):
    # get arguments, stop function if none are found or user is not admin
    arguments = await functions.get_arguments("manage-links", message)
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
        await functions.send_error(message.channel, "Unknown Command", "manage-links")
