"""Prints out usage statistics for ATS.
"""

# from copy import copy
import argparse
import datetime
import database.print_usage
# from optparse import OptionParser
# from optparse import Option, OptionValueError

def date(value):
    return datetime.datetime.strptime(value, '%Y-%m-%d')

def addOptions(parser):
    parser.add_argument(
        '--start_date', action='store', dest='start_date', type=date,
        help='(required) First day of report, in the form YYYY-MM-DD')
    parser.add_argument(
        '--end_date', action='store', dest='end_date', type=date,
        help='(required) Last day of report, in the form YYYY-MM-DD')
    parser.add_argument(
        '--user', action='store', dest='user', default='all',
        help='(optional) Only report on this user (default is all users)')

def check_options(options, parser):
    if options.start_date is None:
        parser.error ('start_date missing')
    if options.end_date is None:
        parser.error ('end_date missing')

def show(start_date, end_date, user):
    stats = database.print_usage.Stats(start_date, end_date, user)
    database.print_usage.write_report(stats)
    database.print_usage.make_charts(stats)

def main():
    parser = argparse.ArgumentParser()
    # parser = OptionParser(version="%prog " + version.version,
    #                       option_class=MyOption)
    addOptions(parser)
    args = parser.parse_args()
    # (options, unused_args) = parser.parse_args()
    check_options(args, parser)
    show(
        start_date = args.start_date,
        end_date   = args.end_date,
        user       = args.user)

if __name__ == "__main__":
    main()
