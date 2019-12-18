""" request.py -- handles the communication with google trend server """

""" TODO
 * Hybrid approach, use a precomputed size, if doesn't work find the new parameters
"""

from .errors import *
from .connection import *
from .aux import *

import datetime
import time
import json
import math
import statistics

### Main function ###

def timeseries(start, end, keyword, granularity='HOUR', geo="", debug=False):
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
            # The chosen granularity is too imprecise - return the one offered by trends instead
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

        if e > et:
            e = et
            s = e - interval_size

        values = timeseries_parser(connection({\
                'granularity': granularity, \
                'start_time': to_datetime(s),\
                'end_time': to_datetime(e),\
                'keywords': keyword,\
                'geo': geo}).run())

        if debug:
            print("From " + to_datetime(s).strftime('%Y-%m-%dT%H:%M:%S') + " to " + to_datetime(e).strftime('%Y-%m-%dT%H:%M:%S'))

        intersect = {key: results[key]['ratio']*results[key]['value'][i]/values[key][i] for i in range(len(keyword)) for key in values if key in results and results[key]['value'] and values[key][i]}
        ratio = 1
        if len(intersect.values()):
            ratio = statistics.mean(intersect.values())
        
        results.update({key: {'time': key, 'value': values[key], 'ratio': ratio} for key in values if int(key) <= et})

    return timeseries_normalizing(results)


### Tests ###

"""
keywords = ["christmas", "santa"]
rslt = timeseries("2015-12-15T00:00:00",  "2016-01-07T00:00:00", keywords, granularity="HOUR", debug=True)
"""
