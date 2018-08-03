import time
from collections import UserList

def bytes2human(bytes, suffix='B'):
    for unit in ['', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi']:
        if abs(bytes) < 1024.00:
            return "%3.2f%s%s" % (bytes, unit, suffix)
        bytes /= 1024.00
    return "%.2f%s%s" % (bytes, 'Yi', suffix)


def coroutine(func):
    def start(*args, **kwargs):
        cr = func(*args, **kwargs)
        next(cr)
        return cr
    return start


def follow(thefile):
    thefile.seek(0, 2) # Go to the end of the file
    while True:
        line = thefile.readline()
        if not line:
            time.sleep(0.1) # Sleep briefly
            continue
        yield line


def earliest_hour(timestamp):
    # Return the timestamp of next hour by the given timestamp
    return (int(timestamp / 3600) + 1) * 3600


def latest_hour(timestamp):
    return int(timestamp / 3600) * 3600


def timestamp2human(timestamp):
    time_local = time.localtime(timestamp)
    dt = time.strftime("%Y-%m-%d %H:%M:%S", time_local)
    return dt


class MessageLists(UserList):
    def __init__(self, initlist, title, columns):
        super().__init__(initlist)
        self.title = title
        self.columns = columns
        self.data.extend([""] * (30 - len(self.data)))
