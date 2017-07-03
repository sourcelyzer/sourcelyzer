#!/usr/bin/env python

import os
import sys
import shutil

stuff_to_clean = [
    '.coverage',
    '.cache',
    'htmlcov',
    'coverage.xml',
    'dist',
    '.tox',
    'sourcelyzer-runner.spec',
    'sourcelyzer.egg-info'
]

for junk in stuff_to_clean:
    print('Deleting: %s' % junk)
    if os.path.exists(junk):
        if os.path.isdir(junk):
            shutil.rmtree(junk)
        else:
            os.remove(junk)

