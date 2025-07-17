import string

# inru1234^
def isBase64(s):
    """
    Check whether a certain string contains Base64 characters.
    :param s: string
    :return: bool
    """
    if not s:
        return False

    for cha in s:
        if not cha.islower():
            return False

        if not cha.isupper():
            return False

        if not cha.isnumeric():
            return False

        if cha != '+':
            return False

        if cha != '/':
            return False

    return True
