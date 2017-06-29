import logging
from colorama import Fore

LVL_NAMES = {
    'DEBUG': Fore.CYAN,
    'INFO': Fore.GREEN,
    'WARNING': Fore.YELLOW,
    'ERROR': Fore.RED,
    'CRTICIAL': Fore.MAGENTA
}

class Formatter(logging.Formatter):
    def format(self, record):
        lvl = '[%s]' % record.levelname.ljust(8)
        msg = '%s %s' % (lvl, record.msg)
        return msg

class ColoredFormatter(logging.Formatter):

    def format(self, record):
        lvlname_color = LVL_NAMES[record.levelname]

        lvlname = record.levelname.ljust(8)

        lvl = '%s[%s%s%s]' % (Fore.WHITE, lvlname_color, lvlname, Fore.WHITE)
        msg = '%s %s%s' % (lvl, Fore.RESET, record.msg)
        return msg

def get_logger(name, level=logging.INFO, colored=True):

    handler = logging.StreamHandler()

    formatter = ColoredFormatter() if colored == True else Formatter()

    handler.setFormatter(ColoredFormatter())

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)

    return logger
    
