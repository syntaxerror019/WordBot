from wordbot import WordBot, auth_users
from logger import log
import commands
from args import create_parser
import jklm
from time import sleep

wordbot = WordBot()
handler = commands.CommandHandler(wordbot)

# Bot Event Handlers:

def on_connect(name, bot_instance):
    log.info(f"{bot_instance.name} connected to server ({name})")


def on_disconnect(name, bot_instance):
    log.warning(f"{bot_instance.name} disconnected from server ({name})")
    import time
    uptime = (time.time() - bot_instance.init_time) / 60
    print(f"\n\n - - - - THIS SCRIPT LASTED FOR {uptime:.2f} MINUTES - - - -\n\n")
    reconnect()


def on_chatter_added(nickname, peer_id, auth, bot_instance):
    bot_instance.send_chat(
        f"""Wsg {nickname}! I'm {bot_instance.name}. Use '/help' to see my commands.\nDiscord: https://discord.gg/Mceh5cXwXG"""  # noqa: E501
    )
    if auth in auth_users:
        bot_instance.mod(peer_id)


def on_chat(nickname, peer_id, auth, message, bot_instance):
    log.chat(f"{nickname} ({peer_id}) [{auth}]: {message}")
    bot_instance.chat.send_message(message, nickname)
    handler.handle(nickname, peer_id, auth, message)


def on_bot_turn(active_id, syllable, bot_instance):
    word, time = bot_instance.find_words(
        syllable,
        bot_instance.used_words,
        bot_instance.invalid_words
    )
    bot_instance.send_word(word)


def on_correct(id, word, bot_instance):
    bot_instance.add_used_word(word)


def on_player_correct(id, word, bot_instance):
    if not bot_instance.check_word(word):
        dur = bot_instance.dictionary.add_word(word)
        bot_instance.send_chat(f"{word} added to dictionary (took {dur:.2f}s)")
    
    result, category, dur = bot_instance.check_categories(word)
    
    if result:
        bot_instance.send_chat(f"{bot_instance.get_name_from_id(id)} placed a(n) {category}: {word} (found in {dur:.2f}s)")

def on_bot_fail(id, reason, bot_instance):
    bot_instance.add_invalid_word(bot_instance.current_word)
    if reason == "notInDictionary":
        bot_instance.dictionary.remove_word(bot_instance.current_word)

    bot_instance.send_chat(f"{bot_instance.current_word} is {reason}, deleted")

    bot_instance.trigger("bot_turn", id, bot_instance.current_syllable)


def on_player_fail(id, reason, bot_instance):
    if reason == "mustContainSyllable":
        handler.handle(None, id, None, bot_instance.current_word)


def round_end(milestone, bot_instance):
    bot_instance.reset_used_words()
    bot_instance.enter_round()


def round_start(milestone, starting_syllable, is_bot_turn, bot_instance):
    if is_bot_turn:
        word, time = bot_instance.find_words(
            starting_syllable,
            bot_instance.used_words
        )
        bot_instance.send_word(word)


# Bind Bot Event Handlers:


def bind_bot_handlers(bot_instance):
    @bot_instance.on("connect")
    def _on_connect(name):
        on_connect(name, bot_instance)

    @bot_instance.on("disconnect")
    def _on_disconnect(name):
        on_disconnect(name, bot_instance)

    @bot_instance.on("chatter_added")
    def _on_chatter_added(nickname, peer_id, username):
        on_chatter_added(nickname, peer_id, username, bot_instance)

    @bot_instance.on("chat")
    def _on_chat(nickname, peer_id, auth, message):
        on_chat(nickname, peer_id, auth, message, bot_instance)

    @bot_instance.on("bot_turn")
    def _on_bot_turn(active_id, syllable):
        on_bot_turn(active_id, syllable, bot_instance)

    @bot_instance.on("bot_correct")
    @bot_instance.on("player_correct")
    def _on_correct(id, word):
        on_correct(id, word, bot_instance)

    @bot_instance.on("player_correct")
    def _on_player_correct(id, word):
        on_player_correct(id, word, bot_instance)

    @bot_instance.on("bot_fail")
    def _on_bot_fail(id, reason):
        on_bot_fail(id, reason, bot_instance)

    @bot_instance.on("player_fail")
    def _on_player_fail(id, reason):
        on_player_fail(id, reason, bot_instance)

    @bot_instance.on("round_end")
    def _round_end(milestone):
        round_end(milestone, bot_instance)

    @bot_instance.on("round_start")
    def _round_start(milestone, starting_syllable, is_bot_turn):
        round_start(milestone, starting_syllable, is_bot_turn, bot_instance)


# Main Function:


def main():
    args = create_parser()

    if args.code is None:
        server_url, args.code = jklm.create_room(
            token=wordbot.token,
            name="WordBot ⚡",
            public=args.public
        )
        log.info("Created a new room.")
    else:
        server_url = jklm.identify_server(args.code)
        log.info("Found an existing room")

    room_url = f"https://jklm.fun/{args.code}"
    room_language = args.language

    log.info(f"Joining room {room_url} @ {server_url} ({room_language})")

    wordbot.set_language(room_language)
    wordbot.connect_room(server_url, args.code)
    wordbot.connect_game(server_url, args.code)
    wordbot.enter_round()

    bind_bot_handlers(wordbot)
    commands.register_command_handlers(handler)

    wordbot.wait()


def reconnect():
    global wordbot
    wordbot.socket.disconnect()
    wordbot.game.disconnect()

    sleep(5)

    wordbot.game = wordbot.return_socket()
    wordbot.socket = wordbot.return_socket()

    wordbot.register_internal_handlers()

    sleep(5)

    wordbot.connect_room(wordbot.room_url, wordbot.code)
    wordbot.connect_game(wordbot.game_url, wordbot.code)
    wordbot.enter_round()

    bind_bot_handlers(wordbot)
    commands.register_command_handlers(handler)

    wordbot.wait()


if __name__ == "__main__":
    main()
