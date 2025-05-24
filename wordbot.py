import misc
import time
import secret
from dictionary import Dictionary
from categories import Categorizer
from discord import Discord
from timing import Timer
from define import define
import re
import socketio


BOT_DISCONNECTED = 0
BOT_CONNECTED = 1
BOT_THINKING = 2

# Player Stats
players_words_correct = {}
players_words_incorrect = {}
players_time_in_game = {}
players_average_response_time = {}

# WordBot Stats
bot_words_played = 0

bot_details = {
    "name": None,
    "id": None,
    "status": None,
    "room": None,
    "language": None,
    "uptime": None,
}

auth_users = [
    "syntaxerror19",  # Discord auth
    "syntaxerror019",  # Twitch auth
    "kappug",
    "wqddle",
    "rynamarole",
    ".lorentz.",
    "caioz10",
    "tzurises",
    "Lorentz"
]

class WordBot:
    def __init__(self, name="WordBot ⚡", mod_peers=None, token=None):
        self.socket = self.return_socket()
        self.game = self.return_socket()

        self.peers = []
        
        self.chat = Discord("https://discord.com/api/webhooks/1068311419608629248/FdlkrRyAi5g1zByM4bC0ITp-uSo9ELt7jT6uFKXMuSPFef6dZN1T6eHR6uZkbhnDMfxe")

        self.used_words = set()
        self.invalid_words = set()

        self.current_word = None
        self.current_syllable = None
        
        self.init_time = time.time()
        self.uptime = 0

        bot_details["status"] = BOT_DISCONNECTED
        bot_details["name"] = name

        self.dictionary = Dictionary("dicts/en.txt")
        self.dictionary.load_words()
        
        self.categorizer = Categorizer("dicts/categories") 

        self.token = token or misc.generate_token()
        self.name = name

        self.handlers = {}  # Stores custom event handlers
        self.name = name

        self.mod_peers = mod_peers
        

        if mod_peers:
            for nickname, id in mod_peers.items():
                self.mod(id)

        self.register_internal_handlers()

    def register_internal_handlers(self):
        @self.socket.on("connect")
        def on_socket_connect():
            bot_details["status"] = BOT_CONNECTED
            self.trigger("connect", "socket")

        @self.game.on("connect")
        def on_game_connect():
            bot_details["status"] = BOT_CONNECTED
            self.socket.emit(
                "getChatterProfiles",
                callback=self.get_chatter_profiles
            )
            self.trigger("connect", "game")

        @self.socket.on("disconnect")
        def on_socket_disconnect():
            bot_details["status"] = BOT_DISCONNECTED
            self.trigger("disconnect", "socket")

        @self.game.on("disconnect")
        def on_game_disconnect():
            bot_details["status"] = BOT_DISCONNECTED
            self.trigger("disconnect", "game")

        @self.game.on("nextTurn")
        def on_next_turn(active_id, syllable, _):
            self.current_syllable = syllable
            if active_id == self.selfid:
                self.trigger("bot_turn", active_id, syllable)
            else:
                self.trigger("player_turn", active_id, syllable)

        @self.socket.on("chat")
        def on_chat(user, message, _):
            self.uptime = time.time() - self.init_time
            if user['peerId'] == self.selfid:
                return
            auth = user['auth']['username'] if user.get('auth') and user['auth'].get('username') else None  # noqa: E501
            self.trigger("chat", user['nickname'], user['peerId'], auth, message)  # noqa: E501

        @self.socket.on("chatterAdded")
        def on_chatter_added(user):
            self.socket.emit(
                "getChatterProfiles",
                callback=self.get_chatter_profiles
            )
            self.trigger(
                "chatter_added",
                user['nickname'],
                user['peerId'],
                user['auth']['username']
                if user.get('auth') and user['auth'].get('username')
                else None
            )

        @self.socket.on("chatterRemoved")
        def on_chatter_removed(user):
            self.socket.emit(
                "getChatterProfiles",
                callback=self.get_chatter_profiles
            )
            self.trigger(
                "chatter_removed",
                user['nickname'],
            )

        @self.game.on("failWord")
        def on_fail(id, reason):
            if id == self.selfid:
                self.trigger("bot_fail", id, reason)
            else:
                self.trigger("player_fail", id, reason)

        @self.game.on("correctWord")
        def on_correct(data):
            id = data['playerPeerId']

            if id == self.selfid:
                self.trigger("bot_correct", id, self.current_word)
            else:
                self.trigger("player_correct", id, self.current_word)

        @self.game.on("setMilestone")
        def on_milestone(milestone, time):
            milestone_event = milestone['name']

            if milestone_event == 'seating':
                self.trigger("round_end", milestone)

            elif milestone_event == 'round':
                self.current_syllable = milestone['syllable']
                self.trigger(
                    "round_start",
                    milestone,
                    milestone['syllable'],
                    milestone['currentPlayerPeerId'] == self.selfid
                )

        @self.game.on('setPlayerWord')
        def on_player_word(id, word):
            word = word.lower().strip()
            if word.startswith('.') or word.startswith('/'):
                self.current_word = word
                return

            word = re.sub(r'[^a-z-]', '', word)
            self.current_word = word

    def set_language(self, language):
        self.language = language
        bot_details["language"] = language

    def connect_room(self, url, code):
        self.room_url = url
        self.code = code
        self.socket.connect(url, transports=['websocket'], socketio_path='socket.io', wait_timeout=10)
        bot_details["room"] = url
        self.socket.emit('joinRoom', {
                'language': 'en-US',
                'nickname': self.name,
                'picture': secret.get_secret("IMAGE"),
                'auth': {
                    'service': "jklm",
                    'token':  secret.get_secret("AUTH_TOKEN")
                },
                'roomCode': code,
                'userToken': self.token,
                'token': '',
            },
            callback=self.on_entry)

    def trigger(self, event_name, *args, **kwargs):
        """Trigger registered high-level event handlers."""
        if event_name in self.handlers:
            for handler in self.handlers[event_name]:
                handler(*args, **kwargs)

    def on(self, event_name):
        """Decorator to register a custom event handler."""
        def decorator(func):
            if event_name not in self.handlers:
                self.handlers[event_name] = []
            self.handlers[event_name].append(func)
            return func
        return decorator

    def connect_game(self, url, code):
        self.game_url = url
        self.code = code
        self.game.connect(url, transports=['websocket'], socketio_path='socket.io', wait_timeout=10)
        bot_details["room"] = url
        self.game.emit("joinGame", data=("bombparty", code, self.token))

    def enter_round(self):
        self.game.emit('joinRound')

    def is_admin(self, auth):
        return auth in auth_users

    def ban_player(self, id):
        print(id)
        self.socket.emit(
            "setUserBanned",
            (id, True),
            callback=noop
        )

    def unban_player(self, id):
        self.socket.emit(
            "setUserBanned",
            (id, False),
            callback=noop
        )

    def kick_player(self, id):
        self.ban_player(id)
        self.unban_player(id)

    def mod(self, id):
        self.socket.emit(
            "setUserModerator",
            (id, True),
            callback=noop
        )

    def unmod(self, id):
        self.socket.emit(
            "setUserModerator",
            (id, False),
            callback=noop
        )
        
    def define_word(self, word):
        timer = Timer()
        timer.start()
        definition = define(word)
        return definition, timer.stop()

    def send_chat(self, message, styles={}):
        if not styles.get('font-weight'):
            styles["font-weight"] = "bold"
        if not styles.get('color'):
            styles["color"] = "#ebe0c7"
        self.socket.emit("chat", (message, styles))

    def check_word(self, word):
        return self.dictionary.check_word(word)

    def get_id_from_name(self, name):
        for peer in self.peers:
            if peer['nickname'] == name:
                return peer['peerId']
        return None # THIS WAS  A -1 before
    
    def get_name_from_id(self, id):
        for peer in self.peers:
            if peer['peerId'] == id:
                return peer['nickname']
        return None
    
    def get_avatar(self, id):
        for peer in self.peers:
            if peer['peerId'] == id:
                if 'picture' in peer:
                    return peer['picture']
        return None

    def get_chatter_profiles(self, data):
        self.peers = data

    def bot_status(self):
        print(bot_details)
        return bot_details

    def on_entry(self, data):
        self.selfid = data['selfPeerId']
        bot_details["id"] = self.selfid

    def add_invalid_word(self, word):
        self.invalid_words.add(word)

    def add_used_word(self, word):
        self.used_words.add(word)

    def reset_used_words(self):
        self.used_words.clear()

    def return_socket(self):
        return socketio.Client(reconnection=True, reconnection_attempts=9900, reconnection_delay=10)  # noqa: E501
        #return socketio.Client(
         #   reconnection=True,
         #   logger=True,
         #   engineio_logger=True
        #)
        
    def wait(self):
        self.socket.wait()
        self.game.wait()

    # game events
    def find_words(
            self, keyword, used_words=set(), invalid_words=set(), amount=1
            ):
        timer = Timer()
        timer.start()

        words = self.dictionary.find_word(
            keyword, used_words, invalid_words
        )[:amount]

        elapsed_time = timer.stop()
        if amount == 1:
            return words[0], elapsed_time

        if amount is None:
            return words, elapsed_time, len(words)
        return words, elapsed_time

    def check_categories(
            self, keyword,
            ):
        timer = Timer()
        timer.start()

        result, category = self.categorizer.check_categories(keyword)
        
        elapsed_time = timer.stop()

        return result, category, elapsed_time

        
       

    def send_word(self, word):
        self.game.emit('setWord', data=(word, True))

def noop(*args, **kwargs):
    pass