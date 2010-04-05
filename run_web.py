#!/usr/bin/env python
'''
Created on Mar 16, 2010

@author: bballantine
'''
import __init__ as common

import os, json
from datetime import datetime
from datetime import timedelta
import cherrypy

TIMEFT_WEB = "%Y-%m-%dT%H:%M:%S.%f"
TIMEFT_SQL = "%Y-%m-%d %H:%M:%S.%f" 
TIMELINE_DELTA = 10;

class WebRoot:
    """
    The web root class cherrypy uses to do stuff
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    _cp_config = {'tools.staticdir.on': True,
              'tools.staticdir.dir': os.path.join(current_dir, 'html'),
              'tools.staticdir.index': 'main.html'}
    
    def __init__(self, sql_file):
        self.sql_file = sql_file

    @cherrypy.expose
    def images(self, starttime=None, endtime=None, count=None, duration=1, jump=0):
        """
        Web service to return images based on a time-range
        """
        conn = common.get_sql_conn(self.sql_file)
        c = self._get_images_cursor(conn, starttime, endtime, count, duration, jump)
        out = []
        for row in c:
            out.append({
                "timestamp": row[1].strftime(TIMEFT_WEB),
                "point": {
                    "lat": row[2], "lon": row[3]},
                    "images": row[5:]})
        c.close()
        conn.close()
        cherrypy.response.headers['Content-Type'] = "text/html"
        return json.dumps(out, indent=4)
    images._cp_config = {'tools.staticdir.on': False}
    
    @cherrypy.expose
    def coordinates(self, starttime=None, endtime=None, count=None, *args, **kwargs):
        """
        Web service to return a list of coordinates for graphing on map and timeline
        """
        conn = common.get_sql_conn(self.sql_file)
        c = self._get_images_cursor(conn, starttime, endtime, count)
        out = {'dateTimeFormat': 'iso8601', 'events': []}
        lasttimestamp = None
        delta = timedelta(0,10) # 10 seconds
        savets = True
        for row in c:
            timestamp = row[1]
            if (savets):
                out['timestamp'] = timestamp.strftime(TIMEFT_WEB)
                savets = False
            if ((not(lasttimestamp) or (timestamp - lasttimestamp) >= delta) or row[4]==1):
                out['events'].append({
                    "start": timestamp.strftime(TIMEFT_WEB),
                    "description": "tagged" if row[4] == 1 else "normal",
                    "point": {
                        "lat": row[2], "lon": row[3]}})
                if row[4] == 0:
                    lasttimestamp = timestamp
        c.close()
        conn.close()
        cherrypy.response.headers['Content-Type'] = "text/html"
        return json.dumps(out, indent=4)
    coordinates._cp_config = {'tools.staticdir.on': False}

    def _get_images_cursor(self, conn, starttime=None, endtime=None, count=None, duration=None, jump=0):
        """
        Helper private method to handle the sql query
        """
        c = conn.cursor()
        values = []
        sql = "select * from images"
        if (starttime):
            sql += " where datetime >= ?"
            starttimeobj = datetime_from_web(starttime)
            if (jump):
                delta = timedelta(0,int(jump))
                starttimeobj += delta
            values.append(starttimeobj)
            if (endtime):
                sql += " and datetime < ?"
                values.append(datetime_from_web(endtime))
            elif (duration):
                sql += " and datetime < ?"
                delta = timedelta(0,int(duration))
                endtimeobj = starttimeobj + delta
                values.append(endtimeobj) 
        if (count):
            sql += " limit ?"
            values.append(count)
        print sql
        c.execute(sql, tuple(values))
        return c
    
    
def datetime_from_web(strtime): 
    """
    Converts a datetime string from the web to a python datetime
    """
    strtime = strtime.replace(' ', 'T')
    # cheap way to make sure it has milliseconds
    if (len(strtime.split('.'))!=2):
        strtime += ".00"
    return datetime.strptime(strtime, TIMEFT_WEB)


def run_web(img_dir, sql_file):
    """
    Configures and then kicks off the cherrypy web server
    TODO - fix config to not be so static
    """
    # Set up site-wide config first
    cherrypy.config.update(
        {'server.socket_host': '192.168.0.197',
         'server.socket_port': 8020,
         'server.thread_pool': 10})
    # Set up local config
    conf ={
        '/img':
        {'tools.staticdir.on': True,
        'tools.staticdir.dir': os.path.abspath(img_dir)}}
    # do it!
    cherrypy.quickstart(WebRoot(sql_file), config=conf)
    

if __name__ == '__main__':
    """
        - example:
            ./run_web.py -b ~/work/darpa/data/finaltest01/out/ -q ~/tmp/images.sqlite3
    """
    parser = common.get_opts()
    opts,args=parser.parse_args()
    run_web(opts.base, opts.sql)