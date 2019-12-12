""" request.py -- handles the communication with google trend server """

""" TODO
 * Test other than hours
 * Hybrid approach, use a precomputed size, if doesn't work find the new parameters
 * Multiple keywords

 
 MAX (tested) seconds for each category

 *** might be missing categories, search is not exhaustive***
 
 MINUTE : 14400
 EIGHT_MINUTE : 115200
 SIXTEEN_MINUTE : 230400
 HOUR : 460800
 DAY : 14745600
 WEEK : 58982400
 MONTH : Upped bound not found

"""

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
    """ For more precise error handling """
    print('  ~~~gRAceFUllY EXiTinG~~~~ ')
    sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)


### Main functions ###

def timeseries(start, end, keyword, granularity="HOUR", geo=""):
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
        
        values = timeseries_parser(connection({'granularity': granularity, 'start_time': datetime.datetime.fromtimestamp(s), 'end_time': datetime.datetime.fromtimestamp(e), 'keywords': keyword, 'geo': geo}).run())
        intersect = {key: results[key]['ratio']*results[key]['value']/values[key] for key in values if key in results and results[key]['value'] and values[key]}
        ratio = 1
        if len(intersect.values()):
            ratio = statistics.mean(intersect.values())

        results.update({key: {'time': key, 'value': values[key], 'ratio': ratio} for key in values if int(key) <= et})


    return results




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


def hybrid_timeseries(start, end, keyword, granularity='HOUR', geo="", debug=False):
    """ Two step timeseries determination : 
            First, recursive on the first interval to find suitable interval size
            Second, iterative over intervals of that size """

    # Should depend on granularity
    baseline = get_baseline(granularity)

    results = {}
    st = datetime.datetime.strptime(start, '%Y-%m-%dT%H:%M:%S').timestamp()
    et = datetime.datetime.strptime(end, '%Y-%m-%dT%H:%M:%S').timestamp()

    st = math.floor(st / baseline) * baseline
    et = math.ceil(et / baseline) * baseline
    et_orig = et

    natural_granularity = None
    # First part : DFS to find suitable interval size
    while True:
        try:
            if debug:
                print("Diving into first segment, of size " + str(et-st) + " seconds")
            values = timeseries_parser(connection(\
                    {'start_time': to_datetime(st),\
                     'end_time': to_datetime(et),\
                     'keywords': keyword,\
                     'geo': geo,\
                     'granularity': granularity}\
                     ).run())
            results.update({key: {\
                    'time': key,\
                    'value': values[key], \
                    'ratio': 1} for key in values})
            break
        except ResolutionIncompatibility as e :
            if natural_granularity is None:
                natural_granularity = e.offered
            et -= (math.ceil((et - st) / (2*baseline))*baseline)
        except ValueError:
            # The chosen granularity is too imprecise - return the natural one instead
            values = timeseries_parser(connection(\
                    {'start_time': to_datetime(st),\
                     'end_time': to_datetime(et_orig),\
                     'keywords': keyword,\
                     'geo': geo,\
                     'granularity': natural_granularity}\
                     ).run())
            results.update({key: {\
                    'time': key,\
                    'value': values[key], \
                    'ratio': 1} for key in values})
            return results
            


    # Second part : BFS to break the interval into segments
    interval_size = et - st
    overlap_size = min(interval_size-2*baseline,4*baseline)
    et = et_orig
    number_of_segments = math.ceil((et - st) / (interval_size - overlap_size))


    if debug:
        print("Found suitable size. Interval size is : " + str(interval_size) + ". Overlap size is : " + str(overlap_size) + ". Number of segments : " + str(number_of_segments))

    for w in range(1, number_of_segments+1):
        s = st + ((interval_size-overlap_size) * w)
        e = s + interval_size

        values = timeseries_parser(connection({\
                'granularity': granularity, \
                'start_time': to_datetime(s),\
                'end_time': to_datetime(e),\
                'keywords': keyword,\
                'geo': geo}).run())

        if debug:
            print("From " + to_datetime(s).strftime('%Y-%m-%dT%H:%M:%S') + " to " + to_datetime(e).strftime('%Y-%m-%dT%H:%M:%S'))

        intersect = {key: results[key]['ratio']*results[key]['value']/values[key] for key in values if key in results and results[key]['value'] and values[key]}
        ratio = 1
        if len(intersect.values()):
            ratio = statistics.mean(intersect.values())
        
        results.update({key: {'time': key, 'value': values[key], 'ratio': ratio} for key in values if int(key) <= et})

    return results


### Companion functions ###

def get_baseline(granularity):
    """ Returns the baseline for a given granularity """
    bls = {'MINUTE': 3600,\
             'EIGHT_MINUTE': 3600,\
             'SIXTEEN_MINUTE': 3600,\
             'HOUR': 3600,\
             'DAY': 86400,\
             'WEEK': 86400,\
             'MONTH': 86400}
    if granularity in bls:
        return bls[granularity]
    raise Error


def to_datetime(ts):
    """ Returns ts (timestamp as a number) as a datetime """
    return datetime.datetime.fromtimestamp(ts)


def smart_split(a,b,gran):
    """ Smartly split interval [a,b] into two intervals with some intersection that make sence for the given granularity """
    
    if b > a:
        return smart_split(b,a,gran)

    baseline = get_baseline(gran)
    

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


def timeseries_parser(raw):
    """ Takes the raw timeseries data from Google and converts it to a useable format """

    data = json.loads(raw[5:])['default']['timelineData']
    return {data[i]['time']: data[i]['value'][0] for i in range(len(data))}


def enumerate_possible_granularities(start_date="2005-01-01T00:00:00", start_interval="3600"):
    """ Search (perhaps non-exhaustively) all possible granularities """
    result = {}
    
    st = datetime.datetime.strptime(start_date, '%Y-%m-%dT%H:%M:%S').timestamp()
    et = st + start_interval
    current_interval = start_interval 

    while to_datetime(et) < datetime.datetime.now():
        try:
            print("INTERVAL : " + str(et-st))
            connection({'start_time': to_datetime(st), 'end_time': to_datetime(et), 'keywords': "TEST", 'geo': "",'granularity': "NONE"}).run()
        except ResolutionIncompatibility as e:
            result[e.offered] = {'max': et-st}
            et += current_interval
            current_interval *= 2
            time.sleep(10)

    return result


### Tests ###

rslt = hybrid_timeseries("2015-12-15T00:00:00",  "2016-01-07T00:00:00", ["christmas"], granularity="HOUR", debug=True)
plt.scatter([int(key) for key in rslt], [rslt[key]['value'] * rslt[key]['ratio'] for key in rslt])
plt.savefig('test.png')
