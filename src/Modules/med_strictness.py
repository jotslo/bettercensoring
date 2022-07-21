from Modules import functions
from confusables import is_confusable

async def filter(message, attachments, embeds, guild_settings, is_edit, client, is_nick):
    filtered_words = []
    phrase_list = []
    iterations = 0

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

    for word in message.split():
        lower_word = word.lower()
        alnum_word = "".join(char * char.isalnum() for char in lower_word)
        iterations += 1

        for bad_word in guild_settings["phrase_blacklist"]:
            # if bad word contains space, add to space list
            if iterations == 1:
                if " " in bad_word:
                    phrase_list.append(bad_word)
                    continue

            # if bad word in given word, add to filter list
            if bad_word in lower_word:
                filtered_words.append(word)
                break
            
            # otherwise, if bypass detection enabled, check for bypasses
            elif guild_settings["bypass_detection"]:
                if bad_word not in alnum_word:
                    if not is_confusable(bad_word, alnum_word):
                        # if no bypasses found, try next word in blacklist
                        continue
                
                # otherwise, add bad word to list and break
                filtered_words.append(word)
        
        # add word to list if is discord invite
        filtered_words += await functions.get_invite(word, guild_settings, client)
    
    # iterate through bad phrases and check if existing in message
    for bad_phrase in phrase_list:
        phrase_found = (
            #message == bad_phrase or
            #message.startswith(bad_phrase + " ") or
            #message.endswith(" " + bad_phrase) or
            #" " + bad_phrase + " " in message
            bad_phrase in message
        )

        # if phrase found in message, add phrase to filtered words list
        if phrase_found:
            filtered_words.append(bad_phrase)
    
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
        if guild_settings["replace_messages"] and not is_edit:
            for word in filtered_words:
                message = message.replace(
                    word,
                    functions.check_replacement(guild_settings["replacement_char"]) * len(word)
                )
            
            message = functions.unhide_whitelist(
                message,
                guild_settings["phrase_whitelist"],
                guild_settings["replacement_char"]
            )
            return functions.remove_tags(message) # return filtered string to be resent

        return "" # return empty string to signal deletion
        
    return functions.unhide_whitelist(
        message,
        guild_settings["phrase_whitelist"],
        guild_settings["replacement_char"]
    ) # return original message to signal ignore