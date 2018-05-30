import re
import curses
import atexit
from math import ceil

from libraries.db import get_logdb
from libraries.formater import format_request_path


class MainWindow(object):
    def __init__(self):
        self.screen = curses.initscr()
        self.selected = 0
        atexit.register(curses.endwin)
        curses.cbreak()
        curses.noecho()
        curses.curs_set(0)
        self.window = self.screen.subwin(0, 0)
        self.window.keypad(1)
        self.window.nodelay(1)
        self._db = get_logdb()

    def display(self):
        self.display_summary()
        self.display_unique_visitors()
        self.display_request_files()
        self.screen.refresh()

    def display_summary(self):
        _str = """  Total Requests  30699 Unique Visitors  106 Unique Files 2177 Referrers 0
             Valid Requests  30699 Init. Proc. Time 2s  Static Files 39   Log Size  4.84 MiB
             Failed Requests 0     Excl. IP Hits    0   Unique 404   5490 Bandwidth 134.26 MiB
             Log Source      access_log
        """
        self.window.addstr(0, 0, _str)

    @property
    def get_xy(self):
        return self.window.getyx()

    def display_unique_visitors(self):
        """"""

    def display_request_files(self):
        """"""
        start_row = self.get_xy[0] + 1
        request_files = self._db.query_request_path()
        request_files = format_request_path(request_files)
        self.window.addstr(start_row, 0, "Requested Files (URLs)", curses.A_REVERSE)
        start_row += 2
        colomns = "{:<5} {:>6} {:>12}  {:<8} {:<9} {}".format("Hits", "%h", "Bandwidth", "Method", "Protocol", "Data")
        self.window.addstr(start_row, 0, colomns)
        start_row += 1
        for file in request_files:
            self.window.addstr(start_row, 0, "{count:<5} {percentage:>6} {bandwidth:>12}  {method:<8} {protocol:<9} {data}".format(**file))

    def listener(self):
        # TODO: add more listening keys
        while True:
            key = self.window.getch()
            if key in [ord('q'), ord('Q')]:
                self.destroy()
                break

    def destroy(self):
        # Don't not end the window again if it's already de-initialized
        if not self.isendwin:
            curses.initscr()
            curses.nocbreak()
            curses.echo()
            curses.endwin()

    @property
    def isendwin(self):
        return curses.isendwin()
