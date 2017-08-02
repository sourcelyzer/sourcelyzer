Sourcelyzer
==========

[![Build Status](https://dev.psikon.org/jenkins/buildStatus/icon?job=Sourcelyzer)](https://dev.psikon.org/jenkins/job/Sourcelyzer/)

Statistics gathering and dashboarding tool for code quality metrics.

Designed from the ground up for simplicity, Sourcelyzer aims to do one thing and one thing well, display nice looking information on your code. 

This project is still in its infancy. 

Requirements
============

* An RDBMS supported SQLAclchemy (currently tested on PostgreSQL).
* Python >= 3.1

Installation
============

First prepare your environment
```
$ git clone https://github.com/sourcelyzer/sourcelyzer.git
$ virtualenv venv -p python3
$ source venv/bin/activate
```

Then edit conf/server.properties to your satisfaction

Next run the install script.

```
$ ./sourcelyzer-install.py
```

And follow the instructions.

Running
=======

Currently only console mode is supported:

```
$ ./sourcelyzer-server.py start-console
```

