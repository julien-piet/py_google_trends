import py_google_trends as pgt
import matplotlib.pyplot as plt

keywords = ["tornado", "hurricane"]
rslt = pgt.timeseries("2015-01-01T00:00:00",  "2019-09-09T00:00:00", keywords, granularity="DAY", debug=True, rate_limit=10)
for i in range(len(keywords)):
    plt.scatter([int(key) for key in rslt], [rslt[key][i] for key in rslt])
plt.savefig('test.png')
