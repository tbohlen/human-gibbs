import re
import json
import os
import matplotlib.pyplot
import numpy

# extracting the data from the printe results of a run_all_trials.
# This is necessary because I screwed up and the json serialization failed!

def extract(fName):
    f = open(fName, 'r')
    content = f.readlines()
    # one regular expression will be used to read in trial starts, and another for likelihoods
    trialStart = re.compile("Runnning trial ([0-9]*).*")
    likelihood = re.compile("Found likelihood: ([-0-9\.]*).*")

    # for each line in the file,  clean it and check to see if it is one of the data-containing lins
    data = [];
    currentTrial = -1
    currentMove = -1
    for line in content:
        line = line.strip()
        trialMatch = trialStart.match(line)
        likelihoodMatch = likelihood.match(line)
        if trialMatch:
            currentTrial += 1
            currentMove = -1
            print "found trial", currentTrial;
            data.append([])
        if likelihoodMatch:
            currentMove += 1
            print "found likelihood", likelihoodMatch.group(1), "for move", currentMove
            data[currentTrial].append(float(likelihoodMatch.group(1)));

    f.close()
    base = "parsed-results"
    name = base
    number = 0
    while os.path.exists(name + ".json"):
        name = base + str(number)
        number += 1
    print "Saving parsed results in", name, ".json"
    resultsFile = open(name + ".json", 'w')
    print "Dumping into file..."
    json.dump(data, resultsFile)
    print "Done."
    resultsFile.close()


"""
Function: makeHist
Makes a histogram of the parsed data in the file fName. The file should contain an array of log probabilities. In addition to the histogram, this function outputs the mean and median of those log probabilities. All this is saved to other-results.txt, while the histogram is saved in hist.png.
"""
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

"""
Function: findGroupNums
Finds the number of groups available to choose between for each move in a given set of trials
"""
def findGroupNums(trials):
    groupNums = []
    for trial in trials:
        trialGroups = []
        moves = trial['moves']
        for move in moves:
            # save the number of groups available at this choice
            num = len(trialGroups) + 1
            if num > 8:
                num = 8
            groupNums.append(num)
            # extend the trialGrops list, if this 
            group = move['new_group']
            if group not in trialGroups:
                trialGroups.append(group)
    return groupNums
