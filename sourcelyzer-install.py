#!/usr/bin/env python
import sys
from docopt import docopt
from sourcelyzer.cli import install

__doc__ = """Sourcelyzer Installer

Usage:
    sourcelyzer-installer [options]

options:
    -h --help   Show this help
    -d --debug  Enable debugging output
"""


if __name__ == '__main__':
    args = docopt(__doc__)
    install(args)


