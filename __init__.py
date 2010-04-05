import os, re, sqlite3
from datetime import datetime
from optparse import OptionParser


# W, NW, N, NE, E, SE, S, SW
CAMS = {'W': '8486A360', 'NW' : '36A8E360', 'N': '252BA360', 
        'NE': '86EBC360', 'E': '0CA6DA60', 'SE': '7AB68360', 
        'S': '2FC88360', 'SW': '8CB6A360'}


class FrameImage(object):
    def __init__(self, timeseq, filename):
        # lil' hack - when we get the timestamp, milliseconds
        # are stored in microseconds field
        # so need to multiply by 1000 to convert to microseconds
        if (timeseq[-2] > 59): timeseq[-2] = 59
        timestamp = apply(datetime, timeseq) 
        self._timestamp = timestamp.replace(microsecond=timestamp.microsecond * 1000)
        self._filename = filename

    def timestamp(self):
        return self._timestamp

    def filename(self):
        return self._filename
  
    def __repr__(self):
        return str(self._timestamp) + " --> " + self._filename


class GPSEvent(object):
    def __init__(self, timestamp_or_string, lat=None, lon=None, tagged=False):
        if (isinstance(timestamp_or_string, datetime)):
            self._timestamp = timestamp_or_string
            self._lat = lat
            self._lon = lon
            self._tagged = tagged
        else:
            timestamp, lat, lon = self._parse_string(timestamp_or_string)
            self.__init__(timestamp, lat, lon, tagged)
  
    def _parse_string(self, eventstr):
        datestr, locstr = eventstr.strip().split(',')
        timestamp = datetime.strptime(datestr, "%Y-%m-%d@%H:%M:%S.%f")
        lat, lon = map(float, locstr.split('@'))
        return timestamp, lat, lon
  
    def is_event(self):
        return self._is_event
  
    def timestamp(self):
        return self._timestamp
  
    def lat(self):
        return self._lat

    def lon(self):
        return self._lon
  
    def __repr__(self):
        return str(self._timestamp) + " @ " + str(self._lat) +\
                ", " + str(self._lon) + " tagged? " + str(self._tagged)


def get_opts():
    usage="""\
      usage: %prog [options] 
      
      Program arguments are optional.
    """
    parser = OptionParser(usage)
    #parser.add_option("-n", "--numcams", 
    #                  help="Number of cameras, or images per frame", 
    #                  type="int", dest="num", default=8)
    #parser.add_option("-s", "--size", default="960x720")
    parser.add_option("-b", "--base", 
                      help="Directory of image folders, where the source comes from", 
                      default=None)
    parser.add_option("-d", "--dest",
                      help="Folder in dir to store output", 
                      default="out")
    #parser.add_option("-t", "--font", 
    #                  help="Path to a font to use")
    parser.add_option("-s", "--start_file",
                      help="Image in video0 to find start sequence")
    #parser.add_option("-e", "--event",
    #                  help="path to event file")
    #parser.add_option("-g", "--gps",
    #                  help="path to timestamped gps file")
    parser.add_option("-i", "--image_count",
                      help="Number of images in the sequence", 
                      type="int", default=0)
    parser.add_option("-q", "--sql",
                      help="sql file for web stuff",
                      default="images.sqlite3") 
    #parser.add_option("-c", "--composite",
    #                  help="Create composite images in output for video generation",
    #                  action="store_true", default=False)
    #parser.add_option("-q", "--sequence",
    #                  help="Create image sequence in output for later stitching",
    #                  action="store_true", default=False)
    #parser.add_option("-m", "--html",
    #                  help="Create a web-based visualization",
    #                  action="store_true", default=False)
    #parser.add_option("-w", "--run_web",
    #                  help="Run the web app",
    #                  action="store_true", default=False)
    #parser.add_option("-O", "--old_way",
    #                  help="old data",
    #                  action="store_true", default=False)
    #parser.add_option("-x", "--xxx",
    #                  help="start generating at frame xxx", 
    #                  type="int", default=0)
    #sizere = re.compile(r'^([0-9]{2,4})x([0-9]{2,4})$')
    #opts,args=parser.parse_args()
    #if not sizere.match( opts.size ):
    #    parser.error("Invalid format for size.  Use WIDTHxHEIGHT" )
    return parser


def create_dir(dir):
    if not os.path.exists(dir):
        os.makedirs(dir)
        
    
def create_frametable(base_dir, cams, start_image=None, image_count=0):
    return frametable(frame_image_list(base_dir, cams),
                      len(cams), start_image, image_count)
    

def frame_image_list(base_dir, cams):
    # first create a list of frame images to sort
    dirs = []
    for cam in cams: 
        dirs.append(os.path.join(base_dir, cam))    
  
    filist = []
    for dir in dirs:
        currcam = []
        for dirname in os.listdir(dir):
            dirpath = os.path.join(dir, dirname)
            if (not(os.path.isdir(dirpath))): continue
            for fname in os.listdir(dirpath):
                currcam.append(FrameImage(
                        map(int, re.split("[_\-\:\.]", fname)[1:-1]),
                        os.path.join(dir, dirname, fname)))
        filist.append(sorted(currcam, 
                key = lambda frameImage: frameImage.timestamp()))
    return filist


def frametable(fimg, num_cams, start_image=None, image_count=0):
    ftable = []
    # load ftable with keyframes from CAM[0]
    n = 0
    for keyframe in fimg[0]:
        if ((start_image == None or 
                keyframe.filename().split("/")[-1] == start_image) 
                and (image_count == 0 or n < image_count)):
            start_image = None
            # add row that looks like [keyframe, None, None,...]
            row = [keyframe]
            row.extend([None for i in range(num_cams - 1)])
            ftable.append(row)
            n += 1
    # add other frames
    for index in range(1, num_cams):
        f = 0
        currf = fimg[index]
        curr_len = len(currf)
        for frame in ftable:
            if (f == curr_len): break
            closest = currf[f]
            while (f+1 < curr_len and
                   not(closer(frame[0],closest,currf[f+1]))):
                f += 1
                if (f == curr_len): break
                closest = currf[f]
            frame[index]=closest
    return ftable


def closer(targetT, t1, t2):
    targetDate = targetT.timestamp()
    date1 = t1.timestamp()
    date2 = t2.timestamp()
    return abs(targetDate-date1) <= abs(targetDate-date2)


def list_cams(cams):
    """
    does default order for cams:
        W, NW, N, NE, E, SE, S, SW
    """
    return list(cams[c] for c in\
                ['W', 'NW', 'N', 'NE', 'E', 'SE', 'S', 'SW'])
    

def get_sql_conn(sql_file):
  return sqlite3.connect(sql_file, detect_types=sqlite3.PARSE_DECLTYPES)
