import re
import curses
import atexit
from math import ceil
import asyncio
import time
import sys
import traceback

from libraries.db import get_logdb
from libraries.utils import bytes2human
from libraries.formater import format_request_path, format_request_status


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
        self.window.scrollok(True)

        self._db = get_logdb()
        self.total_requests = self._db.count()

    def display(self):
        try:
            while True:
                self.display_summary()
                self.display_unique_visitors()
                self.display_request_files()
                self.display_static_files()
                self.display_not_found_files()
                # self.display_http_status()
                self.window.refresh()
                time.sleep(10)
        except Exception as e:
            self.destroy()
            traceback.print_exc()
            sys.exit()

    def display_summary(self):
        # TODO: add summary as below
        _str = """  Total Requests  30699 Unique Visitors  106 Unique Files 2177 Referrers 0
             Valid Requests  30699 Init. Proc. Time 2s  Static Files 39   Log Size  4.84 MiB
             Failed Requests 0     Excl. IP Hits    0   Unique 404   5490 Bandwidth 134.26 MiB
             Log Source      access_log
        """
        self.window.addstr(0, 0, _str)

    @property
    def get_xy(self):
        return self.window.getyx()

    @property
    def new_line(self):
        return self.window.getyx()[0] + 2

    def display_unique_visitors(self):
        """"""

    def _display_request_files(self, request_files, title):
        """"""
        request_files = format_request_path(request_files)
        self.window.addstr(self.new_line, 0, title, curses.A_REVERSE)
        colomns = "{:<5} {:>6} {:>12}  {:<8} {:<9} {}".format("Hits", "%h", "Bandwidth", "Method", "Protocol", "Data")
        self.window.addstr(self.new_line, 0, colomns)
        start_row = self.new_line
        for file in request_files[:3]:
            self.window.addstr(start_row, 0,
                               "{:<5} {:>6,.2%} {:>12}  {:<8} {:<9} {}"
                               .format(file['count'],
                                       float(file['count']/self.total_requests),
                                       bytes2human(file['bandwidth']),
                                       file['method'],
                                       file['protocol'],
                                       file['data']))
            start_row += 1

    def display_request_files(self):
        request_files = self._db.query_request_files()
        self._display_request_files(request_files, "Requested Files (URLs)")

    def display_static_files(self):
        static_files = self._db.query_static_files()
        self._display_request_files(static_files, "Static Requests")

    def display_not_found_files(self):
        not_found_files = self._db.query_not_found_files()
        self._display_request_files(not_found_files, "Not Found URLs (404s)")

    def display_http_status(self):
        status = format_request_status(self._db.query_http_status())


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
