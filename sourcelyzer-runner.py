#!/usr/bin/env python
import sys
from docopt import docopt
from sourcelyzer.cli import runner

__doc__ = """Sourcelyzer Runner

Usage:
    sourcelyzer-runner [options]

Options:
    -h --help               Show this help
    -d --debug              Enable debug output
    -c --config CONFFILE    Location of project config file
    -u --user USERNAME      Sourcelyzer username
    -p --password PASSWORD  Sourcelyzer password
    --url URL               URL to Sourcelyzer
"""

if __name__ == '__main__':
    args = docopt(__doc__)
    runner(args)

