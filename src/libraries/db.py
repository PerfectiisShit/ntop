import sqlite3
from contextlib import closing

_logdb = None


# =================================
# Store messages
# =================================
class LogDB(object):
    def __init__(self, fields):
        self.begin = False
        self.table = "access_log"
        self.report_queries = []
        self.column_list = ','.join(fields)
        self.holder_list = ','.join(':%s' % var for var in fields)
        self.conn = sqlite3.connect(':memory:')
        self.conn.row_factory = sqlite3.Row

    def process(self, raw):
        insert = 'insert into %s (%s) values (%s)' % (self.table, self.column_list, self.holder_list)
        with closing(self.conn.cursor()) as cursor:
            cursor.execute(insert, raw)

    def processmany(self, raws):
        insert = 'insert into %s (%s) values (%s)' % (self.table, self.column_list, self.holder_list)
        with closing(self.conn.cursor()) as cursor:
            cursor.executemany(insert, raws)

    def query(self, sql):
        try:
            with closing(self.conn.cursor()) as cursor:
                cursor.execute(sql)
                data = cursor.fetchall()

            return [dict(i) for i in data]
        except Exception as e:
            print(str(e))
            pass

    @staticmethod
    def build_where_by_timestamp(start=None, stop=None):
        where = ""
        if start and stop:
            where = "AND time_local > %s AND time_local < %s " % (start, stop)
        elif start and not stop:
            where = "AND time_local > %s " % start
        elif not start and stop:
            where = "AND time_local < %s " % stop

        return where

    def query_http_status(self, start, stop):
        """
        :return:  
        [...,
        {'5xx': 0, '3xx': 0, '2xx': 6044, 'bandwidth': 134940931, 'status': '200', 'count': 6044, '4xx': 0},
        {'5xx': 0, '3xx': 176, '2xx': 0, 'bandwidth': 55418, 'status': '301', 'count': 176, '4xx': 0},
        ...]
        """
        where = self.build_where_by_timestamp(start, stop)
        sql = "SELECT status, COUNT(1) AS count," \
              " SUM(body_bytes_sent) AS bandwidth," \
              " COUNT(CASE WHEN status LIKE '2%' THEN 1 END) AS '2xx'," \
              " COUNT(CASE WHEN status LIKE '3%' THEN 1 END) AS '3xx'," \
              " COUNT(CASE WHEN status LIKE '4%' THEN 1 END) AS '4xx'," \
              " COUNT(CASE WHEN status LIKE '5%' THEN 1 END) AS '5xx'" \
              " FROM %s WHERE 1 = 1 %s GROUP BY status" % (self.table, where)
        return self.query(sql)

    def _simple_group_by(self, group_by, start, stop, where='', having='', limit=30):
        where = self.build_where_by_timestamp(start, stop) + where
        sql = "SELECT %s, COUNT(1) AS count, SUM(body_bytes_sent) AS bandwidth " \
              "FROM %s WHERE 1 = 1 %s GROUP BY  %s %s ORDER BY count DESC LIMIT %s"\
              % (group_by, self.table, where, group_by, having, limit)

        return self.query(sql)

    def query_request_files(self, start, stop):
        """
        :return: 
        [
        {'bandwidth': 10129962, 'count': 894, 'request': 'GET /emails/ HTTP/1.1'},
        {'bandwidth': 72628, 'count': 228, 'request': 'GET / HTTP/1.0'}
        ]
        """

        return self._simple_group_by('request', start, stop, where="AND request not like '%/static/%' ")

    def query_static_files(self, start, stop):
        return self._simple_group_by('request', start, stop, where="AND request like '%/static/%' ")

    def query_not_found_files(self, start, stop):
        return self._simple_group_by('request', start, stop, where="AND status = '404' ")

    def query_remote_address(self, start, stop):
        """
        :return: 
        [
        {'bandwidth': 10129962, 'count': 894, 'remote_addr': '192.168.2.2'},
        {'bandwidth': 72628, 'count': 228, 'remote_addr': '1.1.1.1'}
        ]
        """
        return self._simple_group_by('remote_addr', start, stop)

    def query_user_agent(self, start, stop):
        return self._simple_group_by('http_user_agent', start, stop)

    def query_http_referer(self, start, stop):
        """
        :return: 
        [
        {'bandwidth': 10129962, 'count': 894, 'http_referer': 'http://example.com/test},
        {'bandwidth': 72628, 'count': 228, 'http_referer': 'http://example.com/go'}
        ]
        """
        return self._simple_group_by('http_referer', start, stop)

    def init_db(self):
        create_table = 'create table %s (%s)' % (self.table, self.column_list)
        # create_index = 'create index msg_user on messages (user)'
        with closing(self.conn.cursor()) as cursor:
            cursor.execute(create_table)
            # cursor.execute(create_index)

    def count(self, start, stop):
        where = self.build_where_by_timestamp(start, stop)
        with closing(self.conn.cursor()) as cursor:
            cursor.execute('select count(1) as count from %s WHERE 1 = 1 %s' % (self.table, where))
            return cursor.fetchone()['count']

    def query_timerange(self):
        with closing(self.conn.cursor()) as cursor:
            cursor.execute('select min(time_local) as start_time, max(time_local) as end_time from %s' % self.table)
            result = cursor.fetchone()
            return result['start_time'], result['end_time']

    def close(self):
        self.conn.close()


def get_logdb(fields=None):
    global _logdb
    if _logdb is None and fields is None:
        # Expect a fields parameter while accessing this at the first time
        raise ValueError("Can not initialize database without fields provided")
    elif _logdb is None:
        _logdb = LogDB(fields)
        _logdb.init_db()

    return _logdb
