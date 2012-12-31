import re
import json

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
    resultsFName = "parsedResults.json"
    resultsF = open(resultsFName, 'w')
    print "Dumping into file..."
    json.dump(data, resultsF)
    print "Done."
    resultsF.close()



