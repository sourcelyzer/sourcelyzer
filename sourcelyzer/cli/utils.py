import sys, os

def out(msg):
    sys.stdout.write(msg)
    sys.stdout.flush()

def outnl(msg):
    out(msg + os.linesep)

def ask_generic(msg, default=None, valids=None):
    msg = '[x] %s' % msg

    if default != None:
        msg += ' (%s): ' % default

    while True:
        sys.stdout.write(msg)
        sys.stdout.flush()
        user_input = sys.stdin.readline().strip()
        if valids != None and user_input not in valids:
            continue
        elif user_input == "" and default == None:
            continue
        elif user_input == "" and default != None:
            user_input = default
            break
    
    return user_input


def ask_yesno(msg, default=True):

    valids = ['Y','y','n','N']

    yn = 'Y/n' if default == True else 'y/N'

    while True:
        sys.stdout.write('[x] %s [%s]: ' % (msg, yn))
        sys.stdout.flush()

        user_input = sys.stdin.readline().strip()

        if user_input == "":
            user_input = 'Y' if default == True else 'N'

        if user_input not in valids:
            continue
        else:
            break
    
    return True if user_input == 'Y' or user_input == 'y' else False

