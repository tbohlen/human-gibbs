import json
import matplotlib.pyplot
import numpy
import os
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

    # print the mean and median to special file
    base = "other-results"
    number = 0
    name = base + str(number)
    while os.path.exists(name + ".txt"):
        name = base + str(number)
        number += 1
    print "saving other results in", name, ".txt"
    otherFile = open(name + ".txt", 'w')
    otherFile.write("mean: " + str(numpy.mean(combinedData)))
    otherFile.write("median: " + str(numpy.median(combinedData)))

    matplotlib.pyplot.close() # close any open figure windows, just to make sure
    matplotlib.pyplot.autoscale(enable=True, axis="both", tight=True)
    plot = matplotlib.pyplot.hist(combinedData, bins=50)
    base = "hist"
    number = 0
    name = base + str(number)
    while os.path.exists(name + ".png"):
        name = base + str(number)
        number += 1
    print "Saving histogram in", name + ".png"
    matplotlib.pyplot.savefig(name + ".png");
