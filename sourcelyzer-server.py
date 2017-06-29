#!/usr/bin/env python
import sys
from docopt import docopt
from sourcelyzer.cli import server

__doc__ = """Sourcelyzer Server

Usage:
    sourcelyzer-server start [options]
    sourcelyzer-server stop [options]
    sourcelyzer-server restart [options]
    sourcelyzer-server start-console [options]


commands:
    start          Starts the Soucelyzer server
    stop           Stop the Sourcelyzer server
    restart        Restart the Sourcelyzer server
    start-console  Start the server in console mode


options:
    -h --help              Show this help
    -c --config CONFFILE   Location of app.config file
    -d --debug  Enable debugging output
"""


if __name__ == '__main__':
    server(docopt(__doc__))

