""" connection.py -- handles the communication with google trends server """

from errors import *

import requests
import datetime
import time
import json
import math
import statistics

class connection:
    def __init__(self, params):
        if 'start_time' not in params or 'end_time' not in params or 'keywords' not in params:
            raise Exception('start_time, end_time and keyword are required parameters')
        self.start_time = params['start_time']
        self.end_time = params['end_time']
        self.keywords = params['keywords']
        self.granularity = 'HOUR' if 'granularity' not in params else params['granularity']

        self.geo = '' if 'geo' not in params else params['geo']
        self.cookie = None if 'cookie' not in params else params['cookie']
        self.session = requests.Session()

    def build_timeseries_options(self, tkn):
        """ build_timeseries_options : return the URL formatted version of the parameters """
    
        return {'hl': 'en-US', 'tz': 240, 'token': tkn, 'req': '{"time":"' + self.format_times() + '","resolution":"' + self.granularity + '","locale":"en-US","comparisonItem":[{"geo":{},"complexKeywordsRestriction":{"keyword":[{"type":"BROAD","value":"' + self.keywords + '"}]}}],"requestOptions":{"property":"","backend":"CM","category":0}}'}


    def build_explore_options(self):
        """ build_explore_options : return the URL formatted version of the parameters """
    
        return {'hl': 'en-US', 'tz': 240, 'req': '{"comparisonItem":[{"keyword":"'+self.keywords+'","geo":"'+self.geo+'","time":"'+self.format_times()+'"}],"category":0,"property":""}'}


    def format_times(self): 
        """ format_times : return time interval in gtrends format """

        st = self.start_time
        et = self.end_time

        if (st >= et):
            raise ValueError('start_time should be inferior to end_time')

        if ((et - st).days > 8):
            return st.date().strftime('%Y-%m-%d') + " " + et.date().strftime('%Y-%m-%d')
        return st.strftime('%Y-%m-%dT%H\\\\:%M\\\\:%S') + " " + et.strftime('%Y-%m-%dT%H\\\\:%M\\\\:%S')


    def get_token(self):
        """ get_token : fetch api token """

        URL = "https://trends.google.com/trends/api/explore"
        payload = self.build_explore_options()
        headers = {} if not self.cookie else {'cookie': self.cookie}

        r = self.session.get(URL, params=payload, headers=headers)
        
        i = 0
        while i < 10:
            if (r.status_code == 429 and 'set-cookie' in r.headers):
                self.cookie = r.headers['set-cookie'].split(';')[0]
                r = self.session.get(URL, params=payload, headers={'cookie': self.cookie})
            elif (r.status_code == 429):
                # Too many requests. Pause
                break_time = 60*i
                print("Too many requests to Google server. Taking a " + str(break_time) + " second break")
                time.sleep(break_time)
                headers = {} if not self.cookie else {'cookie': self.cookie}
                r = self.session.get(URL, params=payload, headers=headers)
            else:
                break
            i += 1

        if (r.status_code != 200):           
            raise GoogleTrendsServerError(r.text, r.status_code)
        
        return_value = json.loads(r.text[4:])
        for widget in return_value['widgets']:
            if 'id' in widget and widget['id'] == "TIMESERIES":
                if widget["request"]["resolution"] != self.granularity:
                    raise ResolutionIncompatibility(widget["request"]["resolution"],self.granularity)
                return widget['token']
        
        raise Error

    
    def run(self):
        """ run : does the actual trend query """

        URL = "https://trends.google.com/trends/api/widgetdata/multiline"
        payload = self.build_timeseries_options(self.get_token())
        headers = {} if not self.cookie else {'cookie': self.cookie}

        r = self.session.get(URL, params=payload, headers=headers)
        for i in range(3):
            if (r.status_code == 429 and 'set-cookie' in r.headers):
                self.cookie = r.headers['set-cookie'].split(';')[0]
                r = self.session.get(URL, params=payload, headers={'cookie': self.cookie})
            else:
                break

        if (r.status_code != 200):           
            raise GoogleTrendsServerError(r.text)

        return r.text
