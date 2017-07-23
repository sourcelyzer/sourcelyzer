import logging
from datetime import datetime
from colorama import Fore

LOGLVL_COLORMAP = {
    'DEBUG': Fore.CYAN,
    'INFO': Fore.GREEN,
    'WARNING': Fore.YELLOW,
    'ERROR': Fore.RED,
    'CRITICAL': Fore.MAGENTA
}

LOGMSG_COLORMAP = {
    'DEBUG': Fore.LIGHTCYAN_EX,
    'INFO': Fore.RESET,
    'WARNING': Fore.LIGHTYELLOW_EX,
    'ERROR': Fore.LIGHTRED_EX,
    'CRITICAL': Fore.LIGHTMAGENTA_EX
}


class StandardFormatter(logging.Formatter):
    def format(self, record):
        msg = '%s [%s] %s: %s' % (
            datetime.now(),
            record.levelname.ljust(8),
            record.name,
            record.msg
        )
        return msg


class ColoredFormatter(logging.Formatter):

    def format(self, record):
        lvlname_color = LOGLVL_COLORMAP[record.levelname]
        msg_color = LOGMSG_COLORMAP[record.levelname]

        lvl = '%s[%s%s%s]' % (
            Fore.WHITE,
            lvlname_color,
            record.levelname.ljust(8),
            Fore.WHITE
        )

        msg = '%s %s%s%s' % (lvl, msg_color, record.msg, Fore.RESET)
        return msg


def init_logger(name, level=logging.INFO, colored=True, handler=None):

    if handler == None:
        handler = logging.StreamHandler()

    formatter = ColoredFormatter() if colored == True else StandardFormatter()

    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)

        
