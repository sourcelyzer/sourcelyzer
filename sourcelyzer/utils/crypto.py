import hashlib, os, binascii, sys
from argon2 import PasswordHasher

def gen_passwd_hash(pw):
    ph = PasswordHasher(hash_len=hash_length, salt_len=salt_length, encoding=encoding, time_cost=time_cost, memory_cost=memory_cost)
    pwhash = ph.hash(pw)

def verify_hash(pw, hs):
    ph = PasswordHasher()
    ph.verify(hs)

def _console_test(argv):
    pw = argv[1]
    salt_length = int(argv[2])
    hash_length = int(argv[3])

    print('Password:    %s' % pw)
    print('Salt Length: %s' % salt_length)
    print('Hash Length: %s' % hash_length)
    print('------------------------------')
    print('Calculating hash...')

    ph = PasswordHasher(hash_len=hash_length, salt_len=salt_length, encoding='utf-8', time_cost=1000, memory_cost=1024)
    pwhash = ph.hash(pw)

    print('Verifying hash...')

    ph2 = PasswordHasher()

    verified = ph2.verify(pwhash, pw)

    parsed = parse_argon_hash(pwhash)

    print('Results:')
    print('Hash    : %s' % pwhash)
    print('Verified: %s' % verified)
    print('Parsed  : %s' % parsed)
    """
    print('Output:')
    print('Salt  : %s' % salt)
    print('Hash 1: %s' % pwhash)
    print('Hash 2: %s' % pwhash2)
    """

if __name__=='__main__':
    _console_test(sys.argv)
