import sys

sys.path.append( '/usr/apps/ats/7.0.0/lib/python2.7/site-packages/MySQL' )

import datetime

import MySQLdb
import pygal

class Stats(object):
    def __init__(self, start_date, end_date, user='all'):
        self._user = user
        self._sql_start_date = start_date.strftime('%Y-%m-%d')
        self._sql_end_date = end_date.strftime('%Y-%m-%d')

    def get_user(self):
        return self._user

    def get_sql_start_date(self):
        return self._sql_start_date

    def get_sql_end_date(self):
        return self._sql_end_date

    def run_query(self):
        self._db = MySQLdb.connect(
            host="bugzi",
            user="tracker",
            passwd="tracker",
            db="tracker")
        self._cur = self._db.cursor()
        self._cur.execute('SET @start_date      := "%s";' % self._sql_start_date)
        self._cur.execute('SET @end_date        := "%s";' % self._sql_end_date)
        self._cur.execute('SET @user            := "%s";' % self._user)
        self._cur.execute('SET @start_date_time := concat(@start_date, " 00:00:00");')
        self._cur.execute('SET @end_date_time   := concat(@end_date, " 23:59:59");')
        self._cur.execute("""
        # Returns total runtime seconds and total tests, grouped by host within week,
        # with subtotals by week and overall totals.
        SELECT
        # Be sure that the second parameter of [year]week(date, mode) matches:
        # the weekday named in str_to_date AND %x%v vs. %X%V, below!
        str_to_date(concat(yearweek(run.rundate, 3), ' Monday'), '%x%v %W')
                                   AS "Week Starting",
        host.hostName              AS "Host",
        round(sum(run.wallTime),1) AS "Total Secs",
        sum(intv.entry)            AS "Total Tests"
        FROM run

        LEFT JOIN code ON code.codeID=run.codeID
        LEFT JOIN host ON host.hostID=run.hostID
        LEFT JOIN user ON user.userID=run.userID
        # intproperty points at property record.
        # Need to get a temp intproperty record first so we can check the
        # propName of the associated property record and decide if we
        # want the value (intproperty.entry) after all:
        LEFT JOIN intproperty AS tempint ON tempint.runID=run.runID
        LEFT JOIN property    AS intp    ON intp.propID=tempint.propID
        LEFT JOIN intproperty AS intv    ON intv.runID=run.runID
                                        and intp.propName="Tests"
        WHERE code.codeName = "ats"
        AND run.runDate BETWEEN @start_date_time AND @end_date_time
        AND @user = "all" OR user.userName = @user
        GROUP BY `Week Starting`, `Host` WITH ROLLUP
        ;
        """)

    def get_column_names(self):
        """Returns a list of column names"""
        result = []
        for column in self._cur.description:
            result.append(column[0])
        return result

    def fetch_row(self):
        """Returns the current row and moves the cursor to the next.

        Returns Null if there are no more rows.
        """
        return self._cur.fetchone()

    def fetch_all(self):
        """Returns all the rows

        Don't use if the result is "big".
        """
        return self._cur.fetchall()

def write_report(stats):
    """Produces a text report.

    For use by print_usage.demo and by Lib/show_stats
    """
    format_string = '{0[0]:15}  {0[1]:10}  {0[2]:10}  {0[3]:10}'
    print ('ATS usage from %s to %s, for user "%s":' %
           (stats.get_sql_start_date(), stats.get_sql_end_date(), stats.get_user()))
    print ('')
    stats.run_query()
    print (format_string.format(stats.get_column_names()))
    rows = stats.fetch_all()
    for row in rows:
        date, host, secs, tests = row
        if date is None:
            date = 'ALL weeks'
        else:
            date = date.isoformat()
        if host is None:
            host = 'ALL hosts'
        print(format_string.format((date, host, secs, tests)))

def make_charts(stats):

    def combine_weeks(rows):
        """Consolidate data for each week into one row.

        Return secs/tests by host, within week.
        """
        result = {}
        for row in rows:
            date, host, secs, tests = row
            if date is not None and host is not None: # Don't include totals
                date = date.isoformat()
                if date not in result.keys():
                    result[date] = {}
                result[date][host] = (secs, tests)
        return result

    def get_all_hosts(weeks):
        """Returns a list of the unique host names from weeks.
        """
        result_set = set()
        for week_data in weeks.values():
            for host in week_data.keys():
                result_set.add(host)
        return list(result_set)

    def combine_hosts(weeks):
        """Consolidate data for each host into one row

        Return quantity by week, within host, within secs/tests.
        Some hosts will be absent from some input weeks. Provide zero entries for those.
        """
        # Initialize result
        result = dict()
        result['secs'] = dict()
        result['tests'] = dict()
        value_keys = result.keys()
        host_keys = get_all_hosts(weeks)
        week_keys = weeks.keys()
        for value in value_keys:
            for host in host_keys:
                result[value][host] = dict(weeks)
                for week in week_keys:
                    result[value][host][week] = 0
        # Populate result
        for week_key, host_data in weeks.items():
            # Use the actual hosts in this week, not all hosts:
            for host in host_data.keys():
                result['secs'][host][week_key] = host_data[host][0]
                result['tests'][host][week_key] = host_data[host][1]
        return result

    stats.run_query()
    rows = stats.fetch_all() # Grouped by host within date
    weeks_data = combine_weeks(rows)
    hosts_data = combine_hosts(weeks_data)

    charts = {}
    for chart_key in hosts_data.keys():
        charts[chart_key] = pygal.StackedBar()
    charts['secs'].y_title = 'Wall Seconds'
    charts['tests'].y_title = 'Tests Run'
    for chart_key, chart in charts.items():
        chart_data = hosts_data[chart_key]
        host_keys = chart_data.keys()
        host_keys.sort()
        for host_key in host_keys:
            host_data = chart_data[host_key]
            week_keys = host_data.keys()
            week_keys.sort()
            values = list()
            for week_key in week_keys:
                values.append(host_data[week_key])
            chart.add(host_key,values)
        chart.title = "ATS usage by machine within week"
        chart.x_title = 'Week Starting'
        chart.x_labels = week_keys
        chart.x_label_rotation=20
        # chart.value_formatter = lambda x: format(x)
        # chart.value_formatter = lambda x: "%.2f" % x
        chart.render_in_browser()

def demo():
    print("running demo")
    stats = Stats(
        start_date=datetime.date(year=2015, month=1, day=2),
        end_date=datetime.date(year=2015, month=12, day=31))
    write_report(stats)
    make_charts(stats)

if __name__ == "__main__":
    demo()
