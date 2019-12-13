# py_google_trends

## *A python utility for querying google trends data*

py_google_trends provides an API to access Google trends data over any period of time, for any granularity. 

### Installation

Copy the py_google_trends directory to your project, install requirements with :
`pip install -r requirements.txt`

### Usage

Import the module using :
`import py_google_trends as pgt`


The timeseries function included in the package allows to query the Google trends server for a specific set of keywords, across any time frame for any granularity. Syntax :

```
timeseries(start, end, keywords, granularity="HOUR", debug=False)

### Returns ###
A dictionnary, giving for each timestamp between start and end and array containing the popularity of each keyword

### Parameters ###
start       : start date, format : YYYY-MM-DDTHH:MM:SS (ex : 2018-12-31T23:59:59)
end         : end date, same format
keywords    : array of keywords to search for
granularity : resolution of the search
debug       : set to True to enter verbose mode
```

#### Granularity

The granularity parameter allows to select the resolution wanted for the data. For instance, if you want a point of data for each hour in the interval, set granularity to "HOUR". The values allowed by Google are :

`['MINUTE','EIGHT_MINUTE','SIXTEEN_MINUTE','HOUR','DAY','WEEK','MONTH']`

The smaller the granularity, the longer it will take for the utility to get all the data. Furthermore, if you select a granularity that is too large for the given interval (e.g. "MONTH" for a week-long interval), the utility will return data with the largest granularity allowed by Trends.

### Caveat

This is not an official API for google trends. I do not guarantee that the data is accurate, and extensive use might cause a temporary ban from google trend servers. I am not responsible for what you do with the software, use at your own risk.
