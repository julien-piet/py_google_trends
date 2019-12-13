""" aux.py -- companion functions to the main utility """

from .errors import *
from .connection import *

import datetime
import time
import json
import math


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


def timeseries_parser(raw):
    """ Takes the raw timeseries data from Google and converts it to a useable format """

    data = json.loads(raw[5:])['default']['timelineData']
    return {data[i]['time']: data[i]['value'] for i in range(len(data))}


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
