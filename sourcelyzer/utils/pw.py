import hashlib, os


def gen_salt_digest():
    salthash = hashlib.sha512()
    salthash.update(os.urandom(128))
    return salthash.hexdigest()


def gen_salted_pass(pwinput, saltinput):
    pwhash = hashlib.sha512()
    pwhash.update(pwinput)
    pwdigest = pwhash.hexdigest()

    salthash = hashlib.sha512()
    salthash.update(saltinput)
    saltdigest = salthash.hexdigest()

    saltedpass = ''.join([a+b for a,b in zip(pwdigest,saltdigest)])

    saltedhash = hashlib.sha512()
    saltedhash.update(saltedpass.encode('utf8'))
    return saltedhash.hexdigest()


def gen_pass_hash(pwinput):

    salt = gen_salt_digest()

    pwdigest = gen_salted_pass(pwinput, salt.encode('utf8'))

    if len(salt) != len(pwdigest):
        raise RuntimeError("salt and digest should be the same length")

    finalhash = ''.join([a+b for a,b in zip(pwdigest,salt)])
    return finalhash


def compare_pass(pwinput, expecteddigest):

    salt = ""
    for i in range(1,len(expecteddigest),2):
        salt = salt + str(expecteddigest[i])

    pwdigest = gen_salted_pass(pwinput, salt.encode('utf8'))

    finaldigest = ''.join([a+b for a,b in zip(pwdigest,salt)])

    if finaldigest == expecteddigest:
        return True
    else:
        return False

