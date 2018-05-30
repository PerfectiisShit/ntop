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


hits_sort = lambda object: object.hits
