from Modules import functions
from confusables import is_confusable

async def filter(message, attachments, embeds, guild_settings, is_edit, client, is_nick):
    filtered_words = []

    # if filtering nickname and unicode enabled, check for unicode name
    if is_nick:
        if not guild_settings["allow_unicode"]:
            # if any chars are unicode, remove nickname
            if not all(32 <= ord(char) <= 128 for char in message):
                return "Unnamed"

    # for every embed in message, filter content
    if guild_settings["filter_embeds"]:
        for embed in embeds:
            title = embed.title or ""
            description = embed.description or ""
            content = title + " " + description
            new_content = await filter(content, [], [], guild_settings, False, client, False)

            # if content has been filtered, add url to list or schedule msg to be resent
            if content != new_content:
                if embed.url:
                    filtered_words += [functions.strip_link(embed.url)]
                else:
                    message += " "

    # hide whitelist content, compare each word with filter
    message = functions.hide_whitelist(
        message,
        guild_settings["phrase_whitelist"]
    )

    lower_msg = "".join(message.lower().split())
    alnum_msg = "".join(char * char.isalnum() for char in lower_msg)

    for bad_word in guild_settings["phrase_blacklist"]:
        # if bad word in given word, add to filter list
        if bad_word.replace(" ", "") in lower_msg:
            filtered_words.append(bad_word)
            break
        
        # otherwise, if bypass detection enabled, check for bypasses
        elif guild_settings["bypass_detection"]:
            if bad_word.replace(" ", "") not in alnum_msg:
                if not is_confusable(bad_word, alnum_msg):
                    # if no bypasses found, try next word in blacklist
                    continue

            # otherwise, add bad word to list and break
            filtered_words.append(bad_word)

    for word in message.split():
        # add word to list if is discord invite
        filtered_words += await functions.get_invite(word, guild_settings, client)
    
    found_links = await functions.get_message_links(message)
    
    # if link whitelist on, iterate through each link found in message
    if guild_settings["link_whitelist_enabled"]:
        whitelisted_link = False
        for link in found_links:

            # for every whitelisted link, check if link matches
            for good_link in guild_settings["link_whitelist"]:
                if functions.compare_domain(link, good_link):
                    whitelisted_link = True
        
            # if link not whitelisted, add to filtered words list
            if not whitelisted_link:
                filtered_words.append(link)
    
    # otherwise, filter link if in blacklist
    else:
        for link in found_links:
            for bad_link in guild_settings["link_blacklist"]:
                if functions.compare_domain(link, bad_link):
                    filtered_words.append(link)
    
    # censor string contents if necessary and return
    if filtered_words:
        # TEMPORARILY DISABLED
        """if guild_settings["replace_messages"] and not is_edit:
            for word in filtered_words:
                message = message.replace(
                    word,
                    functions.check_replacement(guild_settings["replacement_char"]) * len(word)
                )
            
            message = functions.unhide_whitelist(message, guild_settings["phrase_whitelist"])
            return functions.remove_tags(message) # return filtered string to be resent"""

        return "" # return empty string to signal deletion

    return functions.unhide_whitelist(
        message,
        guild_settings["phrase_whitelist"],
        guild_settings["replacement_char"]
    ) # return original message to signal ignore