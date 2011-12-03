import os, stat, time, tempfile
import hashlib, codecs
import string, re
import psycopg2, psycopg2.extensions


class Connection(object):
    def __init__(self, connstr = None):
        if connstr == None:
            connstr = "dbname='filesys' user='localuser' host='localhost' password='localuser'"
        
        self.connstr = connstr
        
        self.conn = None
        
        self.prepare_re = re.compile('^\s*PREPARE ([A-Z_][A-Z_0-9]*)(\s|[(]).+', re.IGNORECASE)
        self.execute_re = re.compile('^\s*EXECUTE ([A-Z_][A-Z_0-9]*)(\s|[(]|$).*', re.IGNORECASE)
        self.limits = {}


    def connect(self):
        if self.conn:
            return
        
        self.conn = psycopg2.connect(self.connstr)
        self.cursor = self.conn.cursor()


    def begin(self):
        self.conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_SERIALIZABLE)


    def commit(self):
        self.conn.commit()


    def rollback(self):
        self.conn.rollback()


    def prepare(self, sql, min=None, max=10**9):
        self.connect()
        
        try:
            name = self.prepare_re.match(sql).expand('\\1')
            self.limits[name] = min, max
        except AttributeError:
            pass
        
        try:
            self.cursor.execute(sql)
        except Exception, e:
            raise Exception('Error preparing query', e)


    def test_limits(self, sql):
        min,max = None,10**9
        
        try:
            name = self.execute_re.match(sql).expand('\\1')
            min, max = self.limits[name]
        except AttributeError:
            pass
        
        if self.cursor.rowcount < min:
            raise Exception('Too few rows in result')
        if self.cursor.rowcount > max:
            raise Exception('Too many rows in result')


    def execute(self, sql, params = {}):
        self.cursor.execute(sql, params)
        self.test_limits(sql)


    def executemany(self, sql, paramslist = []):
        self.cursor.executemany(sql, paramslist)
        self.test_limits(sql)


    def make_dict_row(self, row):
        if row is None:
            return None
        dictrow = {}
        i = 0
        for f in self.cursor.description:
            dictrow[f[0]] = row[i]
            i = i + 1
        return dictrow


    def fetchall(self):
        rows = self.cursor.fetchall()
        return [self.make_dict_row(row) for row in rows]


    def fetchone(self):
        row = self.cursor.fetchone()
        return self.make_dict_row(row)


    def make_binary(self, data):
        return psycopg2.Binary(data)
