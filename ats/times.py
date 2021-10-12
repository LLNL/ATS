"times: everything to do with timing"
import os, time
from ats.atsut import AtsError
_times_at_start = os.times()
_localtime = time.localtime()
atsStartTime = time.strftime("%y%m%d%H%M%S",_localtime)
atsStartTimeLong = time.strftime('%B %d, %Y %H:%M:%S', _localtime)


def datestamp(long_format=False):
    "Return formatted date and time. Shorter version is just time."
    if long_format:
        return time.strftime('%B %d, %Y %H:%M:%S')
    else:
        return time.strftime('%H:%M:%S')

def hms (t):
    "Returns t seconds in h:m:s.xx"
    #print "DEBUG SAD 000"
    #print t
    #print "DEBUG SAD 010"
    h = int(int(t)/3600.)
    m = int((int(t)-h*3600)/60.)
    s = int((int(t)-h*3600-m*60))
    return "%d:%02d:%02d" %(h,m,s)

def hm (t):
    "Returns t minutes in h:m - used for tM option in batch"
    #print "DEBUG hm 100"
    #print t
    #print "DEBUG hm 110"
    h = int(int(t)/60.)
    m = int(int(t)-h*60)
    return "%d:%02d" %(h,m)

def curDateTime():
    "Return formatted date and time yyyy/mm/dd hh:mm:ss for database"
    return time.strftime('%Y-%m-%d %H:%M:%S')

def wallTimeSecs():
    "Return the wall time used so far in seconds"
    times_at_end = os.times()
    return times_at_end[4] - _times_at_start[4]

def wallTime():
    "Return the wall time used so far in h:mm:ss"
    return hms(wallTimeSecs())

class Duration(object):
    """A duration of time in seconds.

You can create a Duration from, or compare one to, an integer or
string specification such as 1m20s

Example::

    t1 = Duration("12s")
    if t1 < 20:
       ...

"""
    def __init__ (self, value=0):
        self.value = timeSpecToSec(value)

    def __hash__(self):
        return hash(self.value)

    def __gt__(self, other):
        if isinstance(other, Duration):
            return self.value > other.value
        else:
            return self.value > timeSpecToSec(other)

    def __ge__(self, other):
        if isinstance(other, Duration):
            return self.value >= other.value
        else:
            return self.value >= timeSpecToSec(other)

    def __lt__(self, other):
        if isinstance(other, Duration):
            return self.value < other.value
        else:
            return self.value < timeSpecToSec(other)

    def __le__(self, other):
        if isinstance(other, Duration):
            return self.value <= other.value
        else:
            return self.value <= timeSpecToSec(other)

    def __eq__(self, other):
        if isinstance(other, Duration):
            return self.value == other.value
        else:
            return self.value == timeSpecToSec(other)

    def __ne__(self, other):
        if isinstance(other, Duration):
            return self.value != other.value
        else:
            return self.value != timeSpecToSec(other)

    def __str__ (self):
        "This time as a string."
        return timeSecToSpec(self.value)

    def __repr__(self):
        return "Duration('%s')" % timeSecToSpec(self.value)

def timeSecToSpec(value):
    h, r = divmod(value, 3600)
    m, s = divmod(r, 60)
    return "%dh%dm%ds" % (h,m,s)

def timeSpecToSec(spec):
    "Return minutes from an integer or string spec of the form nn h nn m nn s"
    specIn = str(spec)
    spec = str(spec).strip().lower()
    posH = spec.find('h')
    posM = spec.find('m')
    posS = spec.find('s')

    if posH == -1 and posM == -1 and posS == -1:
        spec = spec + 'm'
        posM = spec.find('m')

    try:
        if posH > 0:
            h = int(spec[0:posH])
        else:
            h = 0

        if posM > posH:
            m =  int(spec[posH+1:posM])
        else:
            m = 0
            posM = posH

        if posS > posM:
            s =  int(spec[posM+1:posS])
        else:
            sp = spec[posM+1:]
            if not sp:
                s = 0
            else:
                s = int(sp)

        return (h*3600 + 60 * m + s)
    except Exception as e:
        raise AtsError("Bad time specification: %s" % specIn)
