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



def recursive_ts(start, end, keyword, granularity='H', geo=""):
    """ Recursive version that handles errors """

    print("Trying " + start + " to " + end)
    st = time.mktime(datetime.datetime.strptime(start, '%Y-%m-%dT%H:%M:%S').timetuple())
    et = time.mktime(datetime.datetime.strptime(end, '%Y-%m-%dT%H:%M:%S').timetuple())
    diff = (et - st)

    results = {}

    try:
        values = timeseries_parser(connection({'start_time': datetime.datetime.fromtimestamp(st), 'end_time': datetime.datetime.fromtimestamp(et), 'keywords': keyword, 'geo': geo}).run())
        results.update({key: {'time': key, 'value': values[key], 'ratio': 1} for key in values})

    except GoogleTrendsServerError:
        
        print("Too large")

        m = (st + et) / 2
        end_first = datetime.datetime.fromtimestamp(m + 300).strftime('%Y-%m-%dT%H:%M:%S')
        start_second = datetime.datetime.fromtimestamp(m-300).strftime('%Y-%m-%dT%H:%M:%S')

        first_segment = recursive_ts(start, end_first, granularity, geo)
        second_segment = recursive_ts(start_second, end, granularity, geo)
        
        results.update(first_segment)
        intersect = {key: results[key]['ratio']*results[key]['value']/(second_segment[key]['ratio'] * second_segment[key]['value']) for key in second_segment if key in results and results[key]['value'] and second_segment[key]['value']}
        ratio = statistics.mean(intersect.values())

        results.update({key: {'time': second_segment[key]['time'], 'value': second_segment[key]['value'], 'ratio': ratio * second_segment[key]['ratio']} for key in second_segment})

    finally:
        return results




# rslt = recursive_ts("2015-01-01T00:00:00",  "2019-01-01T00:00:00", "ethereum")
# print(rslt)
rslt = timeseries("2015-01-01T00:00:00",  "2015-03-01T00:00:00", "ethereum")
print(rslt)

# plt.plot([key for key in rslt], [rslt[key]['value'] * rslt[key]['ratio'] for key in rslt])
# plt.savefig('test.png')
