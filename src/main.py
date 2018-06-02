from __future__ import division
import time
import datetime
import argparse

try:
    import configparser as ConfigParser
except ImportError:
    import ConfigParser  # ver. < 3.0

from libraries.log_parser import process_log, build_pattern
from libraries.cwindow import MainWindow


def parse_config():
    parser = argparse.ArgumentParser(description='A tool to parse nginx access access.log')
    parser.add_argument('--path', type=str, required=True,
                        help='The path of nginx access access.log file which you want to parse')
    parser.add_argument('--format', default='common', required=True,
                        help='The name of access.log format you want use to parse access access.log')
    parser.add_argument('--format-file', dest='format_file', type=str,
                        help='If specified, will use the access.log format of this file instead of default config.ini')
    parser.add_argument('--start', type=str,
                        help='Display the access access.log starts from START, ie: 20180702')
    parser.add_argument('--end', type=str,
                        help='Display the access access.log ends at END, ie: 2018070211')
    parser.add_argument('--minutes', type=int,
                        help='If only one of the starts or ends specified, '
                             'display access access.log from START to START+MINS or END-MINS to END')
    args = parser.parse_args()
    if args.start:
        args.start = args.start.ljust(14, '0')
        args.start = int(time.mktime(datetime.datetime.strptime(args.start, "%Y%m%d%H%M%S").timetuple()))

    if args.end:
        args.end = args.end.ljust(14, '0')
        args.end = int(time.mktime(datetime.datetime.strptime(args.end, "%Y%m%d%H%M%S").timetuple()))

    if not args.start and not args.end and not args.minutes:
        args.start = None
        args.end = None
    elif not args.start and args.end and args.minutes:
        args.start = args.end - args.minutes * 60
    elif not args.end and args.start and args.minutes:
        args.end = args.start + args.minutes * 60
    elif args.start and not args.end and not args.minutes:
        args.end = int(time.time())
    elif not args.start and not args.end and args.minutes:
        args.end = int(time.time())
        args.start = args.end - args.minutes
    else:
        print("If --end specified, then you must specify one of --start or --minutes")

    format_file = args.format_file or 'config.ini'
    try:
        config = ConfigParser.ConfigParser()
        config.read(format_file)
        args.format = config.get('LOG_FORMAT', args.format.upper())
    except ConfigParser.NoSectionError:
        print("Could not find '{}' under 'LOG_FORMAT' in the file {}".format(args.format.upper(), format_file))

    return args


if __name__ == "__main__":
    _args = parse_config()
    log_file = _args.path
    log_format = _args.format
    pattern = build_pattern(log_format)
    process_log(log_file, pattern)
    window = MainWindow()
    window.display()

