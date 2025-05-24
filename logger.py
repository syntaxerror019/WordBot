from rich.logging import RichHandler
import logging

logging.addLevelName(25, "CHAT")


def chat(self, message, *args, **kwargs):
    self._log(25, message, args, **kwargs)


logging.Logger.chat = chat

logging.basicConfig(
    level=logging.DEBUG,
    format="%(message)s",
    handlers=[RichHandler()]
)

log = logging.getLogger("rich")
