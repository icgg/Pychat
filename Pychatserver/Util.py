import random
import string
import time
import re

def generate_username(name):
    if re.match('^[a-zA-Z0-9_]+$', name):
        return name
    else:
        return ""


def generate_random_nickname():
    minLenght = 8
    maxLength = 15
    length = random.randint(minLenght, maxLength)

    return ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(length))


def time_text():
    return '[' + time.strftime("%H:%M", time.gmtime(time.time() - (3600 * 4))) + '] '