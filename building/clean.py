#!/usr/bin/env python
import fnmatch
import os
import sys
import shutil

stuff_to_clean = [
    '.coverage',
    '.cache',
    'htmlcov',
    'coverage.xml',
    'reports',
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

matches = []

for root, dirnames, filenames in os.walk('.'):
    for filename in filenames:
        if filename.endswith('.pyc'):
            pyc = os.path.join(root, filename)
            print('Deleting: %s' % pyc)
            os.remove(pyc)
    for dirname in dirnames:
        if dirname == '__pycache__':
            pyc = os.path.join(root, dirname)
            print('Deleting: %s' % pyc)
            shutil.rmtree(pyc)


