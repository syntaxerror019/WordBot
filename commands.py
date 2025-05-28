import jklm

class Command:
    def __init__(self, name, aliases, desc, usage, admin, action):
        self.name = name
        self.aliases = aliases
        self.desc = desc
        self.usage = usage
        self.admin = admin
        self.action = action

    def matches(self, input_command):
        return input_command == self.name or input_command in self.aliases

    def execute(self, *args, **kwargs):
        if self.admin:
            if kwargs.get("bot").is_admin(kwargs.get("auth")):
                self.action(*args, **kwargs)
                return
            else:
                kwargs.get("bot").send_chat("You do not have permission to use this command.")
                return
        self.action(*args, **kwargs)


class CommandHandler:
    def __init__(self, bot):
        self.bot = bot
        self.commands = {}

    def add_command(self, name, aliases, desc, usage, admin, action):
        command = Command(name, aliases, desc, usage, admin, action)
        self.commands[name] = command

    def handle(self, nickname, peer_id, auth, message):
        if not (message.startswith(".") or message.startswith("/")):
            return

        command_parts = message[1:].strip().lower().split()
        input_command = command_parts[0]
        args = command_parts[1:]

        # Find the matching command
        for command in self.commands.values():
            if command.matches(input_command):
                command.execute(nickname=nickname, peer_id=peer_id, auth=auth, args=args, bot=self.bot)
                return

        self.bot.send_chat(f"Unknown command: '{input_command}'. Type '/help' for a list of commands.")

    def show_help(self, nickname, peer_id, auth, args, bot):
        if args:
            requested_command = args[0]
            command = self.commands.get(requested_command) # Check the command list.
            if not command: # If its not in the command list, check the aliases.
                for cmd in self.commands.values():
                    if requested_command in cmd.aliases:
                        command = cmd
                        break
            if command:
                bot.send_chat(
                    f"""'{command.name}':\n   ‣ {command.desc}\n   ‣ Usage: {command.usage}\n   ‣ Aliases: {", ".join(command.aliases)}\n   ‣ Admin only: {command.admin}"""
                )
            else:
                bot.send_chat(f"Unknown command: '{requested_command}'. Type '/help' for a list of commands.")
        else:
            command_list = [f"/{cmd.name}" for cmd in self.commands.values()]
            bot.send_chat("Available commands:\n" + " — ".join(command_list) + "\nType '/help <command>' for more information.")
            

def register_command_handlers(handler):
    handler.add_command(
        "help",
        ["h"],
        "Displays a list of commands.",
        "/help",
        admin=False,
        action=handler.show_help,
    )
    handler.add_command(
        "search",
        ["c"],
        "Search for words containing a syllable.",
        "/search <syllable>",
        admin=False,
        action=search_action,
    )
    handler.add_command(
        "kick",
        ["k"],
        "Kicks a player from the game.",
        "/kick <player_name>",
        admin=True,
        action=lambda nickname, peer_id, auth, args, bot: bot.kick_player(bot.get_id_from_name(args[0]) if args else bot.send_chat("Usage: /kick <player_name>")),
    )
    handler.add_command(
        "ban",
        ["ba"],
        "Bans a player permanently.",
        "/ban <player_name>",
        admin=True,
        action=lambda nickname, peer_id, auth, args, bot: bot.ban_player(bot.get_id_from_name(args[0]) if args else bot.send_chat("Usage: /ban <player_name>")),
    )
    handler.add_command(
        "unban",
        ["ub"],
        "Unbans a player.",
        "/unban <player_name>",
        admin=True,
        action=lambda nickname, peer_id, auth, args, bot: bot.unban_player(bot.get_id_from_name(args[0]) if args else bot.send_chat("Usage: /unban <player_name>")),
    )
    handler.add_command(
        "mod",
        ["mo"],
        "Make a user a moderator.",
        "/mod <player_name>",
        admin=True,
        action=lambda nickname, peer_id, auth, args, bot: bot.mod(bot.get_id_from_name(args[0]) if args else bot.send_chat("Usage: /mod <player_name>")),
    )
    handler.add_command(
        "unmod",
        ["um"],
        "Remove a user's moderator status.",
        "/unmod <player_name>",
        admin=True,
        action=lambda nickname, peer_id, auth, args, bot: bot.unmod(bot.get_id_from_name(args[0]) if args else bot.send_chat("Usage: /unmod <player_name>")),
    )
    handler.add_command(
        "status",
        ["s"],
        "Displays the current status of the server.",
        "/status",
        admin=False,
        action=lambda nickname, peer_id, auth, args, bot: bot.send_chat(str(bot.bot_status())),
    )
    handler.add_command(
        "boom",
        ["x"],
        "Show the boom emoji.",
        "/boom",
        admin=False,
        action=lambda nickname, peer_id, auth, args, bot: bot.send_chat("💥"),
    )
    handler.add_command(
        "create",
        ["b"],
        "Create your own room with the bot.",
        "/create",
        admin=False,
        action=lambda nickname, peer_id, auth, args, bot: create_room(nickname, peer_id, auth, args, bot),
    )
    handler.add_command(
        "define",
        ["d"],
        "Define a word.",
        "/define <word>",
        admin=False,
        action=lambda nickname, peer_id, auth, args, bot: define_word(nickname, peer_id, auth, args, bot),
    )
    handler.add_command(
        "eval",
        ["ev"],
        "Execute code snippet.",
        "/eval <code>",
        admin=True,
        action=evaluate,
    )
    handler.add_command(
        "about",
        ["ab"],
        "About the bot.",
        "/about",
        admin=False,
        action=about,
    )
    

def search_action(nickname, peer_id, auth, args, bot):
    if args:
        result, time, amount = bot.find_words(args[0], used_words=bot.used_words, invalid_words=bot.invalid_words, amount=None)
        bot.send_chat(f"Found {amount} words for '{args[0]}' in {time:.2f}s:\n{', '.join(result[:5])}")
    else:
        result, time, amount = bot.find_words(bot.current_syllable, used_words=bot.used_words, invalid_words=bot.invalid_words, amount=None)
        bot.send_chat(f"Found {amount} words for '{bot.current_syllable}' in {time:.2f}s:\n{', '.join(result[:5])}")
    
def create_room(nickname, peer_id, auth, args, bot):
    if nickname is None:
        bot.send_chat("You must be logged in with Discord or Twitch to use this command.")
        return

    url, code = jklm.create_room(
        token=bot.token,
        name=f"WordBot ⚡ x {nickname}",
        public=True
    )
    
    bot.send_chat(f"Room created! Join at {url} with code https://jklm.fun/{code.upper()}")

def evaluate(nickname, peer_id, auth, args, bot):
    print(args)
    try:
        exec(" ".join(args))
    except Exception as e:
        bot.send_chat(str(e))
    
def define_word(nickname, peer_id, auth, args, bot):
    if args:
        word = args[0]
        definition, dur = bot.define_word(word)
        if definition is not None:
            bot.send_chat(f"Definition of '{word}': {definition} (found in {dur:.2f}s)")
        else:
            bot.send_chat(f"Definition not found for '{word}'.")
    else:
        bot.send_chat("Usage: /define <word>")

def about(nickname, peer_id, auth, args, bot):
    bot.send_chat("\n⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\nWordBot rev. 2 (2025)\nCreated by Miles H.\nhttps://www.mileshilliard.com/ & https://wordbot.sntx.dev/\n⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\nAll Rights Reserved 2022-2025 Miles Hilliard")