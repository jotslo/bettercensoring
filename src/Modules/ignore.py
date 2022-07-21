import json
from Modules import functions, data


async def add(message, guild_settings, arguments):
    # check for roles/channels and check whether any exist
    roles, channels = await functions.split_roles_channels(
        " ".join(arguments),
        message.attachments,
        message.guild
    )

    if roles or channels:
        rc_limit = 20000 if guild_settings["is_pro"] else 2000
        new_roles = list(set(guild_settings["ignored_roles"] + roles))
        new_chnls = list(set(guild_settings["ignored_channels"] + channels))
        new_roles.sort()
        new_chnls.sort()

        # if within role/channel limit, add to db, otherwise show an error
        total = len(roles) + len(channels)
        if len(new_roles) + len(new_chnls) <= rc_limit:
            functions.set_data(
                "UPDATE guild_settings SET ignored_roles = (?) WHERE guild_id = (?)",
                (json.dumps(new_roles), guild_settings["guild_id"], )
            )
            functions.set_data(
                "UPDATE guild_settings SET ignored_channels = (?) WHERE guild_id = (?)",
                (json.dumps(new_chnls), guild_settings["guild_id"], )
            )
            await functions.send_embed(
                message.channel,
                "<:thumbs_up:703358705089118299> Role/Channel Blacklist Updated",
                "Successfully added **{0}** new role/channel{1} to your blacklist.".format(
                    total,
                    "s" * (total != 1),
                )
            )
        else:
            await functions.send_embed(
                 message.channel,
                 "⚠️ Role/Channel Limit Reached",
                 data.link_limit[guild_settings["is_pro"]]
             )

    else:
        await functions.send_error(message.channel, "No Roles/Channels Found", "ignore-roles")


async def remove(message, guild_settings, arguments):
    # check for roles/channels and check whether any exist
    roles, channels = await functions.split_roles_channels(
        " ".join(arguments),
        message.attachments,
        message.guild
    )

    if roles or channels:
        new_roles = functions.remove_from_list(
            guild_settings["ignored_roles"],
            roles
        )
        new_chnls = functions.remove_from_list(
            guild_settings["ignored_channels"],
            channels
        )

        # add to db, otherwise show an error
        functions.set_data(
            "UPDATE guild_settings SET ignored_roles = (?) WHERE guild_id = (?)",
            (json.dumps(new_roles), guild_settings["guild_id"], )
        )
        functions.set_data(
            "UPDATE guild_settings SET ignored_channels = (?) WHERE guild_id = (?)",
            (json.dumps(new_chnls), guild_settings["guild_id"], )
        )

        total = len(roles) + len(channels)
        await functions.send_embed(
            message.channel,
            "<:thumbs_up:703358705089118299> Role/Channel Blacklist Updated",
            "Successfully removed **{0}** role/channel{1} from your blacklist.".format(
                total,
                "s" * (total != 1),
            )
        )

    else:
        await functions.send_error(message.channel, "No Roles/Channels Found", "ignore-roles")


async def view(message, guild_settings, arguments):
    # if there are values in ignorelist, return contents
    if guild_settings["ignored_roles"] or guild_settings["ignored_channels"]:
        roles, channels = functions.get_roles_channels(guild_settings)
        await functions.send_embed(
            message.channel,
            "Ignored Roles/Channels",
            "**Roles:**\n{0}\n\n**Channels:**\n{1}\n\n{2}".format(
                "\n".join(roles) if roles else "No Ignored Roles",
                "\n".join(channels) if channels else "No Ignored Channels",
                "To learn how to modify to your ignore list, click **[here](https://censoring.io/commands#ignore-roles)**."
            )
        )
    # otherwise, return error
    else:
        await functions.send_error(
            message.channel,
            "No Roles/Channels Found",
            "ignore-roles"
        )


command_list = {
    "add": add,
    "remove": remove,
    "view": view,
    "list": view,
    "blacklist": add,
    "whitelist": remove
}


async def run(message, guild_settings):
    # get arguments, stop function if none are found or user is not admin
    arguments = await functions.get_arguments("ignore-roles", message)
    if not (arguments and await functions.is_admin(message, guild_settings)):
        return
    
    # if command exists, run associated function
    if arguments[0] in command_list.keys():
        await command_list[arguments[0]](
            message,
            guild_settings,
            arguments[1:]
        )
    else:
        await functions.send_error(message.channel, "Unknown Command", "ignore-roles")
