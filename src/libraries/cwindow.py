import curses
import atexit
import sys
import traceback

from libraries.db import get_logdb
from libraries.utils import bytes2human, earliest_hour, latest_hour, timestamp2human as ts2h, MessageLists
from libraries.formater import format_request_path, format_request_status
from libraries import constants


class MainWindow(object):
    def __init__(self):
        self.screen = None
        self.init_screen()
        self.height, self.width = self.screen.getmaxyx()
        self.summary_window = curses.newwin(7, self.width, 0, 0)
        self.help_window = curses.newwin(2, self.width, (self.height - 2), 0)
        self.window = curses.newwin(200, self.width, 7, 0)
        self.window.keypad(1)
        self.window.nodelay(1)
        self.window.scrollok(True)
        self.window.idlok(True)

        self.selected = 0
        self.show_details = False

        self.titles = []
        self.messages = []

        self.curses_pos_x = 0

        self._db = get_logdb()
        self.start_time, self.end_time = self._db.query_timerange()
        self.start = None
        self.stop = None

    def init_screen(self):
        try:
            self.screen = curses.initscr()
            curses.start_color()
            atexit.register(curses.endwin)
            curses.cbreak()
            curses.noecho()
            curses.curs_set(0)
            curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_YELLOW)
        except:
            sys.exit()

    @property
    def total_requests(self):
        return self._db.count(self.start, self.stop)

    @property
    def current_line(self):
        return self.window.getyx()[0]

    @property
    def new_line(self):
        return self.window.getyx()[0] + 1

    @property
    def messages_length(self):
        return len(self.messages)

    @property
    def max_lines(self):
        return 14 * len(self.messages) if not self.show_details else 14 * len(self.messages) + 20

    def move_cursor(self):
        if self.selected < self.messages_length - 1:
            self.selected += 1
        else:
            self.selected = 0

    def init_cursor(self):
        self.selected = 0
        self.show_details = False
        self.curses_pos_x = 0

    def highlight_line(self, line):
        return line + " " * (self.width - len(line))

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
        self.get_request_files()
        self.get_static_files()
        self.get_not_found_files()

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

    def display_messages(self):
        pos_x = 0
        for index, messages in enumerate(self.messages):
            title = messages.title
            columns = messages.columns
            if self.selected == index:
                mode = curses.color_pair(1)
            else:
                mode = curses.A_REVERSE

            if self.selected == index and self.show_details:
                _messages = messages[:]
            else:
                _messages = messages[:10]

            self.window.addstr(pos_x, 0, title, mode)
            pos_x += 2

            self.window.addstr(pos_x, 0, columns)
            pos_x += 1

            for message in _messages:
                self.window.addnstr(pos_x, 0, message, self.width - 1)
                pos_x += 1

            pos_x += 1

    def get_request_files(self):
        title = self.highlight_line("Requested Files (URLs)")
        columns = "{:<5} {:>6} {:>12}  {:<8} {:<9} {}".format("Hits", "%h", "Bandwidth", "Method", "Protocol", "Data")
        request_files = self._db.query_request_files(self.start, self.stop)
        request_files = format_request_path(request_files, self.total_requests)
        messages = MessageLists(request_files, title, columns)
        self.messages.append(messages)

    def get_static_files(self):
        title = self.highlight_line("Static Requests")
        columns = "{:<5} {:>6} {:>12}  {:<8} {:<9} {}".format("Hits", "%h", "Bandwidth", "Method", "Protocol", "Data")
        static_files = self._db.query_static_files(self.start, self.stop)
        static_files = format_request_path(static_files, self.total_requests)
        messages = MessageLists(static_files, title, columns)
        self.messages.append(messages)

    def get_not_found_files(self):
        title = self.highlight_line("Not Found URLs (404s)")
        columns = "{:<5} {:>6} {:>12}  {:<8} {:<9} {}".format("Hits", "%h", "Bandwidth", "Method", "Protocol", "Data")
        not_found_files = self._db.query_not_found_files(self.start, self.stop)
        not_found_files = format_request_path(not_found_files, self.total_requests)
        messages = MessageLists(not_found_files, title, columns)
        self.messages.append(messages)

    def get_http_status(self):
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
                if self.curses_pos_x < self.max_lines - 2:
                    self.curses_pos_x += 1
                    self.scrolldown()
            elif key == constants.KEY_FORWARD:
                self.init_cursor()
                self.goto_next_hour()
            elif key == constants.KEY_BACKWARD:
                self.init_cursor()
                self.goto_previous_hour()
            elif key == constants.KEY_BACK:
                self.init_cursor()
                self.start = self.stop = None
                self.refresh()
            elif key == constants.KEY_DETAILS:
                self.show_details = not self.show_details
                self.refresh_messages()
            elif key == constants.KEY_TAB:
                self.move_cursor()
                self.refresh_messages()

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

    def refresh_messages(self):
        self.window.clear()
        self.display_messages()
        self.window.refresh()
        self.display_help()

    @property
    def isendwin(self):
        return curses.isendwin()
