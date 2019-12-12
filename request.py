""" request.py -- handles the communication with google trend server """


from errors import *
from connection import *

import requests
import datetime
import time
import json
import math
import statistics
import matplotlib.pyplot as plt

import signal
import sys
def signal_handler(sig, frame):
    print('gRAceFUllY EXiTinG')
    sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)

def timeseries_parser(raw):
    """ Takes the raw timeseries data from Google and converts it to a useable format """

    data = json.loads(raw[5:])['default']['timelineData']
    return {data[i]['time']: data[i]['value'][0] for i in range(len(data))}


def timeseries(start, end, keyword, granularity="H", geo=""):
    """ Obtain the timeseries for that period at the given granularity """
    # Only for Hour granularity at the moment

    segment = (8*24*3600)-3600
    overlap = 23*3600

    st = time.mktime(datetime.datetime.strptime(start, '%Y-%m-%dT%H:%M:%S').timetuple())
    et = time.mktime(datetime.datetime.strptime(end, '%Y-%m-%dT%H:%M:%S').timetuple())
    diff = (et - st)

    results = {}
    for w in range(math.floor(diff / (segment-overlap)) + 1):
        s = st + ((segment-overlap) * w)
        e = s + segment
        
        values = timeseries_parser(connection({'start_time': datetime.datetime.fromtimestamp(s), 'end_time': datetime.datetime.fromtimestamp(e), 'keywords': keyword, 'geo': geo}).run())
        intersect = {key: results[key]['ratio']*results[key]['value']/values[key] for key in values if key in results and results[key]['value'] and values[key]}
        ratio = 1
        if len(intersect.values()):
            ratio = statistics.mean(intersect.values())

        results.update({key: {'time': key, 'value': values[key], 'ratio': ratio} for key in values if int(key) <= et})


    return results


def smart_split(a,b,gran):
    """ Smartly split interval [a,b] into two intervals with some intersection that make sence for the given granularity """
    
    if b > a:
        return smart_split(b,a,gran)

    baseline = 3600

    if a%baseline != 0 or b%baseline != 0:
        raise Error

    # If the gap is too small, we cannot build two interleaving intervals
    if a - b <= 2*baseline:
        raise Error

    # gap size is the size of the intersection. 
    gap_size = min( a - b - 2*baseline , 4*baseline )
    
    middle = (a+b)/2
    a2 = math.ceil( (middle + (gap_size/2)) / baseline ) * baseline
    b2 = math.floor((middle - (gap_size/2)) / baseline ) * baseline

    return [a,a2,b2,b]


def recursive_ts(start, end, keyword, granularity='HOUR', geo="", debug=False):
    """ Recursive version that handles errors """

    if debug:
        print("Trying " + start + " to " + end)
    
    st = time.mktime(datetime.datetime.strptime(start, '%Y-%m-%dT%H:%M:%S').timetuple())
    et = time.mktime(datetime.datetime.strptime(end, '%Y-%m-%dT%H:%M:%S').timetuple())
    diff = (et - st)

    results = {}

    try:
        values = timeseries_parser(connection({'start_time': datetime.datetime.fromtimestamp(st), 'end_time': datetime.datetime.fromtimestamp(et), 'keywords': keyword, 'geo': geo,'granularity': granularity}).run())
        results.update({key: {'time': key, 'value': values[key], 'ratio': 1} for key in values})
    except ResolutionIncompatibility:
        
        if debug :
            print("Too large - Breaking into two intervals")

        split = smart_split(st,et,granularity)
        end_first = datetime.datetime.fromtimestamp(split[1]).strftime('%Y-%m-%dT%H:%M:%S')
        start_second = datetime.datetime.fromtimestamp(split[2]).strftime('%Y-%m-%dT%H:%M:%S')

        first_segment = recursive_ts(start, end_first, keyword, granularity, geo, debug)
        second_segment = recursive_ts(start_second, end, keyword, granularity, geo, debug)
        if len(first_segment) and len(second_segment):
            results.update(first_segment)
            intersect = {key: results[key]['ratio']*results[key]['value']/(second_segment[key]['ratio'] * second_segment[key]['value']) for key in second_segment if key in results and results[key]['value'] and second_segment[key]['value']}
            ratio = statistics.mean(intersect.values())
            results.update({key: {'time': second_segment[key]['time'], 'value': second_segment[key]['value'], 'ratio': ratio * second_segment[key]['ratio']} for key in second_segment})
        else:
            results.update(first_segment)
            results.update(second_segment)

    finally:
        return results




rslt = recursive_ts("2015-12-01T00:00:00",  "2016-02-01T00:00:00", "christmas", debug=True)
#rslt = timeseries("2015-01-01T00:00:00",  "2016-01-01T00:00:00", "ethereum")

# rslt = timeseries_parser(connection({'start_time': datetime.datetime.strptime("2015-01-01T00:00:00", '%Y-%m-%dT%H:%M:%S'), 'end_time': datetime.datetime.strptime("2015-01-08T00:00:00", '%Y-%m-%dT%H:%M:%S'), 'keywords': "TEST", 'geo': ""}).run())

print(rslt)
plt.plot([key for key in rslt], [rslt[key]['value'] * rslt[key]['ratio'] for key in rslt])
plt.savefig('test.png')
