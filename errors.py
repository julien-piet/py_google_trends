""" errors.py -- custom error handling for google trends responses """


class Error(Exception):
   """Base class for other exceptions"""
   pass


class GoogleTrendsServerError(Error):
   """Raised when the google trends server returns an error"""
   def __init__(self,  message="NOT SPECIFIED", code="NOT SPECIFIED"):
       print(message[0:100])
       print(code)
       self.message = message
   

class ResolutionIncompatibility(Error):
    """Raised when the offered resolution is not the one specified"""
    def __init__(self, offered, wanted):
        self.offered = offered;
        self.wanted = wanted
