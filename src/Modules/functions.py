import discord, sqlite3, json
from Modules import data
from re import sub

async def send_embed(channel, title, description):
    embed = discord.Embed(
        title = title,
        description = description,
        colour = 0xff6a00
    )
    embed.set_footer(text = data.version + " by @jotslo | bc:help | censoring.io")
    return await channel.send(embed = embed)


async def send_error(channel, error, command_type):
    await send_embed(
        channel,
        f"⚠️ {error}",
        f"To view command usage, click **[here](https://censoring.io/commands#{command_type})**."
    )


def set_data(command, args):
    # open db, execute, save and close
    database = sqlite3.connect("Source/data.db")
    cursor = database.cursor()
    cursor.execute(command, args)
    database.commit()
    database.close()


def get_data(command, args):
    # open db, execute, fetch response and close
    database = sqlite3.connect("Source/data.db")
    cursor = database.cursor()
    cursor.execute(command, args)
    all_data = cursor.fetchall()
    database.close()

    # if data is in useless list, remove list
    if all_data:
        if len(all_data) == 1 and isinstance(all_data, list):
            return all_data[0]
    
    return all_data


def get_settings(guild_id):
    # get settings data, put into dict format and return
    settings = get_data("SELECT * FROM guild_settings WHERE guild_id = (?)", (str(guild_id), ))
    if settings:
        return {
            "guild_id": settings[0] if settings[0] is not None else 0,
            "phrase_blacklist": json.loads(settings[1] or "[]"),
            "replace_messages": settings[2] if settings[2] is not None else 0,
            "bypass_detection": int(settings[3]) if settings[3] is not None else 1, # remove cast later!
            "filter_nicknames": settings[4] if settings[4] is not None else 1,
            "filter_strictness": settings[5] if settings[5] is not None else 1,
            "ignored_roles": json.loads(["[\""+settings[6]+"\"]",settings[6]][settings[6][0]=="["]or"[]")if settings[6]else[], # handle move to list format
            "phrase_whitelist": json.loads(settings[7] or "[]"),
            "link_whitelist_enabled": settings[8] if settings[8] is not None else 0,
            "link_whitelist": json.loads(settings[9] or "[]"),
            "link_blacklist": json.loads(settings[10] or "[]"),
            "filter_embeds": settings[11] if settings[11] is not None else 1,
            "allow_unicode": settings[12] if settings[12] is not None else 1,
            "allow_invites": settings[13] if settings[13] is not None else 1,
            "is_pro": settings[14] if settings[14] is not None else 0,
            "mute_requirement": settings[15] if settings[15] is not None else 0,
            "kick_requirement": settings[16] if settings[16] is not None else 0,
            "ban_requirement": settings[17] if settings[17] is not None else 0,
            "filter_images": settings[18] if settings[18] is not None else 1,
            "filter_webpages": settings[19] if settings[19] is not None else 1,
            "filter_files": settings[20] if settings[20] is not None else 1,
            "extension_whitelist_enabled": settings[21] if settings[21] is not None else 0,
            "extension_whitelist": json.loads(settings[22] or "[]"),
            "extension_blacklist": json.loads(settings[23] or "[]"),
            "replacement_char": settings[24] or "\*",
            "ignored_channels": json.loads(["[\""+settings[25]+"\"]",settings[25]][settings[25][0]=="["]or"[]")if settings[25]else[], # handle move to list format
        }


def get_roles_channels(guild_settings):
    # iterate through ignored roles and channels, then return
    roles = [f"- <@&{role}>" for role in guild_settings["ignored_roles"]]
    channels = [f"- <#{chnl}>" for chnl in guild_settings["ignored_channels"]]
    return roles, channels


def remove_from_list(main_list, remove_list):
    # iterates through all values to remove and removes if found
    for value in remove_list:
        if value in main_list:
            main_list.remove(value)
    return main_list


def remove_tags(message):
    # remove important tags from message to prevent abuse
    message = message.replace("@everyone", "everyone").replace("@here", "here")
    for word in message.split():
        if "@&" in word:
            message = message.replace(word, "@redacted-role")
    return message


def check_replacement(message):
    # add backslash to replacement to avoid visual issues
    if message == "*":
        message = message.replace("*", "\\*")
    return message


def read_phrase_file(attachment):
    phrases_found = []

    # attempt to convert from json and get phrases
    try:
        for phrase in json.loads(attachment):
            stripped_phrase = phrase.strip()
            if len(stripped_phrase) >= 1 and stripped_phrase not in phrases_found:
                phrases_found += [phrase.strip()]
    
    # if not json, treat as text file and split by newline/comma
    except:
        is_newline = attachment.count("\n") > attachment.count(",")
        for phrase in attachment.split("\n" if is_newline else ","):
            stripped_phrase = phrase.strip()
            if len(stripped_phrase) >= 1 and stripped_phrase not in phrases_found:
                phrases_found += [phrase.strip()]
    
    return phrases_found


def hide_whitelist(message, whitelist):
    # temporarily obfuscate whitelisted words to prevent blacklist
    for word in range(len(whitelist)):
        message = message.replace(whitelist[word], f"/85-;/({word})/;-58/")
    
    # return obfuscated message
    return message


def unhide_whitelist(message, whitelist, replacement):
    # replace obfuscated phrases with original whitelisted words
    for word in range(len(whitelist)):
        message = message.replace(f"/85-;/({word})/;-58/", whitelist[word])
    
    # replace dodgy links (https://\*\*\* etc with ***** as expected)
    for word in message.split():
        if "://\\" in word or ".\*\*" in word or ".\#\#" in word:
            message = message.replace(word, replacement * (len(word) // 2))
    
    # return de-obfuscated message
    return message


async def get_phrases(message, attachments):
    phrases_found = []

    # iterate through comma-separated message and add phrases
    for phrase in message.split(","):
        stripped_phrase = phrase.strip()
        if len(stripped_phrase) >= 1 and stripped_phrase not in phrases_found:
            phrases_found += [phrase.strip()]
    
    # iterate through files, check size < 20KB and add to list
    for attachment in attachments:
        if 1 <= attachment.size <= 20000:
            given_file = await attachment.read()
            phrases = read_phrase_file(given_file.decode("utf-8"))
            if phrases:
                phrases_found += phrases
    
    return phrases_found


async def find_role(guild, value, stripped_value):
    # check value type and search for role accordingly
    if len(stripped_value) == 18 and stripped_value.isdigit():
        # check if role exists, and return if applicable
        associated_role = guild.get_role(int(stripped_value))
        if associated_role:
            return associated_role
    
    # otherwise, check for role with exact name
    lower_value = value.lower()
    lower_stripped = stripped_value.lower()
    for role in guild.roles:
        if role.name.lower() == lower_value:
            return role


async def find_channel(guild, value, stripped_value):
    # check value type and search for channel accordingly
    if len(stripped_value) == 18 and stripped_value.isdigit():
        # check if channel exists, and return if applicable
        associated_chnl = guild.get_channel(int(stripped_value))
        if associated_chnl:
            return associated_chnl
    
    # otherwise, check for channel with exact name
    lower_value = value.lower()
    lower_stripped = stripped_value.lower()
    for chnl in guild.channels:
        if chnl.name.lower() == lower_value:
            return chnl


async def split_roles_channels(message, attachments, guild):
    roles = []
    channels = []
    
    # call get_phrases to split arguments
    values_found = await get_phrases(message, attachments)

    # iterate through arguments, check ids/names and add to lists
    for value in values_found:
        stripped_value = "".join([c * c.isalnum() for c in value])
        relevant_role = await find_role(guild, value, stripped_value)

        # if role is found, add to role list, else check for channels
        if relevant_role:
            roles += [str(relevant_role.id)]
        else:
            relevant_chnl = await find_channel(guild, value, stripped_value)
            if relevant_chnl:
                channels += [str(relevant_chnl.id)]
            
    return roles, channels


async def get_invite(word, guild_settings, client):
    # if server doesn't allow invites, get last section of word
    if not guild_settings["allow_invites"]:
        
        # check if word starts with discord link for basic checking
        if any(word.startswith(link) for link in data.discord_links):
            return [word]
        
        # otherwise, attempt to get invite code from word
        invite = "".join(x * x.isalnum() for x in word.split("/")[-1])

        # if word is of invite link length then continue
        if 7 <= len(invite) <= 10:
            has_digit = any(c.isdigit() for c in invite)
            has_cap = any(c.isupper() for c in invite[1:])

            # if word has cap or digit, check via discord for invite
            if has_cap or has_digit:

                # if no error, invite exists, return invite
                try:
                    await client.fetch_invite(invite)
                    return [word]
                
                # invite does not exist, return empty list
                except Exception as e:
                    return []

    # otherwise, just return empty list
    return []


def strip_link(link):
    # remove www and useless chars if tld and link valid
    if "://" in link:
        link = link.split("://")[1]
    link = link.strip("/").split(".")
    tld = link[-1].split("/")[0]
    if tld.upper() in data.tlds and len(link) > 1:
        if link[0] == "www":
            return ".".join(link[1:])
        else:
            return ".".join(link)


def compare_domain(msg_link, bad_link):
    # check if bad domain in user-sent link and return bool
    return msg_link.split("/")[0].endswith(bad_link.split("/")[0])
    

async def get_links(message, attachments):
    # call get_phrases to get contents
    links_found = await get_phrases(message, attachments)
    validated_links = []

    # check if tld and link is valid, remove www and useless chars
    for link in links_found:
        new_link = strip_link(link)
        if new_link:
            validated_links += [new_link]
    
    return validated_links


async def get_message_links(message):
    # split message by spaces to find possible links
    links_found = message.split()
    validated_links = []

    # check if tld and link is valid, remove www and useless chars
    for link in links_found:
        new_link = strip_link(link)
        if new_link:
            validated_links += [new_link]

    return validated_links


async def is_admin(message, guild_settings):
    # return true if user is admin, otherwise return error
    if message.author.guild_permissions.administrator:
        return True

    await send_embed(
        message.channel,
        "⚠️ Invalid Permissions",
        "You do not have permissions to configure the bot."
    )


async def get_arguments(command_type, message):
    # check message arguments, return error if none given
    arguments = message.content.lower().split()[1:]
    if not arguments:
        await send_error(message.channel, "Missing Arguments", command_type)
    return arguments


async def get_webhook(bot, channel, webhook_list):
    # if webhook exists, return
    for webhook in webhook_list:
        if webhook.user == bot and webhook.channel_id == channel.id:
            return webhook
    
    # otherwise, create new webhook and return
    new_webhook = await channel.create_webhook(
        name = "BetterCensoringMessageReplacement",
        reason = "This webhook is used to mimic users when they send inappropriate messages."
    )
    return new_webhook
