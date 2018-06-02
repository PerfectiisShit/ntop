import re
import curses
import atexit
from math import ceil
import asyncio
import time
import sys
import traceback

from libraries.db import get_logdb
from libraries.utils import bytes2human, earliest_hour, latest_hour, timestamp2human as ts2h
from libraries.formater import format_request_path, format_request_status
from libraries import constants


class MainWindow(object):
    def __init__(self):
        self.screen = curses.initscr()
        self.height, self.width = self.screen.getmaxyx()
        atexit.register(curses.endwin)
        curses.cbreak()
        curses.noecho()
        curses.curs_set(0)
        self.summary_window = curses.newwin(7, self.width, 0, 0)
        self.help_window = curses.newwin(2, self.width, (self.height - 2), 0)
        self.window = curses.newwin(50, self.width, 7, 0)
        self.window.keypad(1)
        self.window.nodelay(1)
        self.window.scrollok(True)
        self.window.idlok(True)

        self.selected = 0
        self.show_details = False

        self.messages = []

        self.curses_pos_x = 0

        self._db = get_logdb()
        self.start_time, self.end_time = self._db.query_timerange()
        self.start = None
        self.stop = None

    @property
    def total_requests(self):
        return self._db.count(self.start, self.stop)

    @property
    def current_line(self):
        return self.window.getyx()[0]

    @property
    def new_line(self):
        return self.window.getyx()[0] + 1

    def display_summary(self):
        # TODO: add summary as below
        start = self.start or self.start_time
        stop = self.stop or self.end_time
        title = "Dashboard - Overall Analyzed Requests (%s - %s)" % (ts2h(start), ts2h(stop))
        _str = """  Total Requests  30699 Unique Visitors  106 Unique Files 2177 Referrers 0
        Valid Requests  30699 Init. Proc. Time 2s  Static Files 39   Log Size  4.84 MiB
        Failed Requests 0     Excl. IP Hits    0   Unique 404   5490 Bandwidth 134.26 MiB
        Log Source      access_log
        """
        self.summary_window.clear()
        self.summary_window.addstr(0, 0, self.highlight_line(title), curses.A_REVERSE)
        self.summary_window.addstr(2, 0, _str)
        self.summary_window.refresh()

    def display_help(self):
        self.help_window.clear()
        _help = "Press [q/Q] to exit, [h/H] for help"
        pos_y = int((self.width - len(_help)) / 2)
        self.help_window.addstr(1, pos_y, _help, curses.A_REVERSE)
        self.help_window.refresh()

    def goto_next_hour(self):
        if self.start is None and self.stop is None:
            self.start = self.start_time
            self.stop = earliest_hour(self.start_time)
        elif self.stop < self.end_time:
            self.start = self.stop
            self.stop += 3600

        self.refresh()

    def goto_previous_hour(self):
        if self.start is None and self.stop is None:
            self.start = latest_hour(self.end_time)
            self.stop = self.end_time
        elif self.start > self.start_time:
            self.stop = self.start
            self.start -= 3600

        self.refresh()

    def pre_display(self):
        self.display_request_files()
        self.display_static_files()
        self.display_not_found_files()

    def display(self):
        try:
            self.display_summary()
            self.window.clear()
            self.pre_display()
            self.display_messages()
            self.window.refresh()
            self.display_help()
            self.listener()
        except Exception as e:
            self.destroy()
            traceback.print_exc()
            sys.exit()

    def display_unique_visitors(self):
        """"""

    def highlight_line(self, line):
        return line + " " * (self.width - len(line))

    # def _display_request_files(self, request_files, title):
    #     """"""
    #     total_requests = self.total_requests
    #     request_files = format_request_path(request_files)
    #     self.window.addstr(self.new_line + 1, 0, self.highlight_line(title), curses.A_REVERSE)
    #     colomns = "{:<5} {:>6} {:>12}  {:<8} {:<9} {}".format("Hits", "%h", "Bandwidth", "Method", "Protocol", "Data")
    #     self.window.addstr(self.new_line, 0, colomns)
    #     for file in request_files[:10]:
    #         self.window.addnstr(self.new_line, 0,
    #                             "{:<5} {:>6,.2%} {:>12}  {:<8} {:<9} {}"
    #                             .format(file['count'],
    #                                     float(file['count']/total_requests),
    #                                     bytes2human(file['bandwidth']),
    #                                     file['method'],
    #                                     file['protocol'],
    #                                     file['data']),
    #                             self.width - 1)

    def display_messages(self):
        pos_x = 0
        for messages in self.messages:
            self.window.addstr(pos_x, 0, messages[0], curses.A_REVERSE)
            pos_x += 1
            for message in messages[1:]:
                self.window.addnstr(pos_x, 0, message, self.width - 1)
                pos_x += 1

    def display_request_files(self):
        messages = []
        title = "Requested Files (URLs)"
        colomns = "{:<5} {:>6} {:>12}  {:<8} {:<9} {}".format("Hits", "%h", "Bandwidth", "Method", "Protocol", "Data")
        request_files = self._db.query_request_files(self.start, self.stop)
        request_files = format_request_path(request_files, self.total_requests)
        messages.append(self.highlight_line(title))
        messages.append("")
        messages.append(colomns)
        messages.extend(request_files[:7])
        messages.extend([""] * (10 - len(messages)))
        messages.append("")
        self.messages.append(messages)

    def display_static_files(self):
        messages = []
        title = "Static Requests"
        colomns = "{:<5} {:>6} {:>12}  {:<8} {:<9} {}".format("Hits", "%h", "Bandwidth", "Method", "Protocol", "Data")
        static_files = self._db.query_static_files(self.start, self.stop)
        static_files = format_request_path(static_files, self.total_requests)
        messages.append(self.highlight_line(title))
        messages.append("")
        messages.append(colomns)
        messages.extend(static_files[:7])
        messages.extend([""] * (10 - len(messages)))
        messages.append("")
        self.messages.append(messages)

    def display_not_found_files(self):
        messages = []
        title = "Not Found URLs (404s)"
        colomns = "{:<5} {:>6} {:>12}  {:<8} {:<9} {}".format("Hits", "%h", "Bandwidth", "Method", "Protocol", "Data")
        not_found_files = self._db.query_not_found_files(self.start, self.stop)
        not_found_files = format_request_path(not_found_files, self.total_requests)
        messages.append(self.highlight_line(title))
        messages.append("")
        messages.append(colomns)
        messages.extend(not_found_files[:7])
        messages.extend([""] * (10 - len(messages)))
        messages.append("")
        self.messages.append(messages)

    def display_http_status(self):
        status = format_request_status(self._db.query_http_status(self.start, self.stop))

    def scrolldown(self):
        self.window.scroll(1)
        self.window.refresh()
        self.display_help()

    def scrollup(self):
        self.window.scroll(-1)
        self.window.refresh()
        self.display_help()

    def listener(self):
        # TODO: add more listening keys
        while True:
            key = self.window.getch()
            if key in [ord('q'), ord('Q')]:
                self.destroy()
                break
            # TODO: how to scroll downward???
            elif key == curses.KEY_UP:
                if self.curses_pos_x >= 1:
                    self.curses_pos_x -= 1
                    self.scrollup()
            elif key == curses.KEY_DOWN:
                if self.curses_pos_x < len(self.messages) - 2:
                    self.curses_pos_x += 1
                    self.scrolldown()
            elif key == constants.KEY_FORWARD:
                self.goto_next_hour()
            elif key == constants.KEY_BACKWARD:
                self.goto_previous_hour()
            elif key == constants.KEY_BACK:
                self.start = self.stop = None
                self.refresh()

    def destroy(self):
        # Don't not end the window again if it's already de-initialized
        if not self.isendwin:
            curses.initscr()
            curses.nocbreak()
            curses.echo()
            curses.endwin()

    def refresh(self):
        self.messages = []
        self.display_summary()
        self.window.clear()
        self.pre_display()
        self.display_messages()
        self.window.refresh()
        self.display_help()

    @property
    def isendwin(self):
        return curses.isendwin()
