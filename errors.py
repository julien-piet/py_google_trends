""" errors.py -- custom error handling for google trends responses """


class Error(Exception):
   """Base class for other exceptions"""
   pass


class GoogleTrendsServerError(Error):
   """Raised when the google trends server returns an error"""
   pass

