#!/usr/bin/env python
'''
Created on Apr 6, 2010

@author: brian
'''

import __init__ as common
import gen_web, run_web, composite
import sys, os, threading

BASE_DIR    = "/media/disk/out"
EVENT_FILE  = "" 
GPS_FILE    = "/media/disk/LOCATION-LOG.2010-04-01@18:16:31.229.log"
SQL_FILE    = "/tmp/images.sqlite3"
FONT_FILE   = "FreeMonoBold.ttf"

if __name__ == '__main__':
    cams = common.list_cams(common.CAMS)
    ftable = common.create_frametable(BASE_DIR, cams)
    if len(sys.argv) == 3 and sys.argv[1] == "composite":
        common.create_dir(sys.argv[2])
        composite.write_images(ftable, sys.argv[2], "960x720", 
                 len(cams), FONT_FILE) 
    else:
        tagged_hash = gen_web.taggedhash(ftable, gen_web.gpsevents(EVENT_FILE, True))
        gps_hash = gen_web.gpshash(ftable, gen_web.gpsevents(GPS_FILE))
        gps_hash.update(tagged_hash)
        gen_web.create_db(SQL_FILE, len(cams))
        gen_web.load_db(SQL_FILE, ftable, gps_hash)
        thread = threading.Thread(target=lambda: os.system("firefox http://localhost:8020"))    
        thread.start()
        run_web.run_web(BASE_DIR, SQL_FILE)
