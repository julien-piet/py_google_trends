import py_google_trends as pgt
import matplotlib.pyplot as plt

keywords = ["christmas", "santa"]
rslt = pgt.timeseries("2015-12-15T00:00:00",  "2016-01-07T00:00:00", keywords, granularity="HOUR", debug=True)
for i in range(len(keywords)):
    plt.scatter([int(key) for key in rslt], [rslt[key][i] for key in rslt])
plt.savefig('test.png')
