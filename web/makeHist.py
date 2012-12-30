import json
import matplotlib.pyplot
import numpy
def makeHist(fName):
    # read in the results
    data = json.load(open(fName, 'r'))
    # compine all likelihoods
    combinedData = []
    for d in data:
        combinedData[-1:-1] = d
    # find info about data
    print "data is", combinedData
    print "mean is", numpy.mean(combinedData)
    print "median is", numpy.median(combinedData)
    histData = matplotlib.pyplot.hist(combinedData, bins=50)
    matplotlib.pyplot.savefig("hist.png");
