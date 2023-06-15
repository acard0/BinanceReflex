import time
import CONFIG

def getMs():
    return time.time_ns() / 1e+6

def cprint(level, msg):
    if (level == 0):
        print(f'INFO: {msg}')
    if (level == 1):
        print(f'WARNING: {msg}')
    if (level == 2):
        print(f'FAIL: {msg}')
    if (level == 3):
        print(f'INFO: {msg}')
    if (level == 4):
        print(f'INFO: {msg}')   