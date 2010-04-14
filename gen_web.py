#!/usr/bin/env python
'''
Created on Mar 16, 2010

@author: brian
'''
import __init__ as common
import os, threading
import run_web

def taggedhash(ftable, events):
    """
    Returns a hash of GPSEvents, one for each tagged event
    Hash keys are timestamps
    """
    n = 0
    gps_hash = {}
    frames_len = len(ftable)
    for event in events:
        closest = ftable[n][0]
        while (n+1<frames_len and
               not(common.closer(event, closest, ftable[n+1][0]))):
            n+=1
            closest = ftable[n][0]
        gps_hash[closest.timestamp()] = event
    return gps_hash

def gpshash(ftable, events):
    """
    Matches gps readings with frames.
    Returns a hash of GPS locations, one item for each frame
    """
    n = 0
    gps_hash = {}
    events_len = len(events)
    for frame in ftable:
        closest = events[n]
        while(n+1<events_len and not(common.closer(frame[0],closest,events[n+1]))):
            n+=1
            closest=events[n]
        gps_hash[frame[0].timestamp()] = closest
    return gps_hash

def gpsevents(gpsfile=None, istagged=False):
    """
    Return a sorted list of GPSEvents given the path to a file of data
    gpsfile should have timestamped gps coordinates, 
    one on each line as follows:
    2010-03-04@16:10:32.804,40.71167333333333@-73.993245
    2010-03-04@16:11:08.551,40.70618@-73.99017333333333
    2010-03-04@16:24:12.221,40.681415@-73.96160666666667
    """
    if not(gpsfile) or len(gpsfile) == 0: return []
    fgps = open(gpsfile, 'r')
    lines = fgps.readlines()
    events = []
    for coord in lines:
        events.append(common.GPSEvent(coord, tagged=istagged))
    events.sort(key=lambda taggedevent: taggedevent.timestamp())
    fgps.close()
    return events

def create_db(sql_file, numcams):
    conn = common.get_sql_conn(sql_file)
    c = conn.cursor()
    # make a property for each camera
    camstr = ", ".join(list("cam" + str(i) + " text" for i in range(numcams)))
    c.executescript(
        "drop table if exists images; " +\
        "create table images ( " +\
          "id INTEGER PRIMARY KEY, " +\
          "datetime TIMESTAMP, " +\
          "lat REAL, lon REAL, is_tagged INTEGER DEFAULT 0, " +\
          camstr + ");")
    conn.commit()
    c.close()
    conn.close()

def load_db(sql_file, ftable, eventhash):
    conn = common.get_sql_conn(sql_file)
    c = conn.cursor()
    n = 0
    for frame in ftable:
        sql = "insert into images values (?,?,?,?,?," + \
          ",".join('?' for i in range(len(frame))) + ")"
        values = [n, frame[0].timestamp()]
        event = eventhash[frame[0].timestamp()] if frame[0].timestamp() in eventhash else None
        if event:
            values += [event.lat(), event.lon(), event.is_tagged()]
        else:
            values += [None,None,None]
        values += list("/".join(f.filename().split("/")[-3:]) for f in frame)
        c.execute(sql,values)
        n += 1
    conn.commit()
    c.close()
    conn.close()
    
def get_more_opts(parser):
    """
    Gets options specific to this module
    """
    parser.add_option("-E", "--event",
                      help="path to event file")
    parser.add_option("-G", "--gps",
                      help="path to timestamped gps file")
    parser.add_option("-R", "--run",
                      help="Run web server and launch the browser",
                      action="store_true", default=False)
    opts,args=parser.parse_args()
    return opts,args 


if __name__ == '__main__':
    """
        - example:
            ./gen_web.py -b ~/work/darpa/data/finaltest01/out/ -G ~/work/darpa/data/finaltest01/LOCATION-LOG.2010-03-04@16:05:35.789.log -E ~/work/darpa/data/finaltest01/GPSTEST-TAGFILE.2010-03-04@16:10:32.784.log -q ~/tmp/images.sqlite3
    """
    # gather command line options
    parser = common.get_opts()
    opts, args = get_more_opts(parser)
    # re-order list of cams for web display
    cams = common.list_cams(common.CAMS)
    # order frames and put in a "frame table"
    ftable = common.create_frametable(opts.base, cams,
                                      opts.start_file, opts.image_count)
    # get default gps and events files
    fevents = opts.event if opts.event else\
        os.path.join(opts.base, "GPSTEST-TAGFILE.log") 
    fgps = opts.gps if opts.gps else\
        os.path.join(opts.base, "LOCATION-LOG.log") 
    # parse gps and tag files for use
    tagged_hash = taggedhash(ftable, gpsevents(fevents, True))
    gps_hash = gpshash(ftable, gpsevents(fgps))
    gps_hash.update(tagged_hash)
    # create and load db w/ frame table and gps info
    create_db(opts.sql, len(cams))
    load_db(opts.sql, ftable, gps_hash)    
    # run the website and launch firefox if we are asked to do that
    if (opts.run):        
        thread = threading.Thread(target=lambda: os.system("firefox http://localhost:8020"))    
        thread.start()
        run_web.run_web(opts.base, opts.sql)
