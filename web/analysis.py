import db
import imageGen
import json
import operator
import os
import time
from PIL import Image
from math import floor, exp
from numpy import *
from scipy.stats import t, truncnorm

mu0 = 255.0 / 2.0 # prior mean
l0 = 90 # confidence in prior mean
sig_sq0 = (256.0 / 4.0)**2 # prior variance
a0 = 90 # confidence in prior variance

DISPERSION_PARAMETER = 100.0

walk_in = 40
samples = 5

"""
Function: get_image_matrix

Gets the image representing a matrix from the image's image_id.  Memoizes the
responses to not waste time

Parameters:
image_id - id of the image to get a matrix representation of

Returns:
Numpy.ndarray of the image
"""
image_matrices = {}
def get_image_matrix(image_id):
    # make sure not an ObjectId
    image_id = str(image_id)

    # check if have already calculated the image matrix for it
    if image_id in image_matrices:
        return image_matrices[image_id]
    # calculate the matrix for it, store it, and return it
    else:
        image_file = db.get_image_file(image_id)
        image_matrices[image_id] = array(imageGen.loadImage(image_file))
        return image_matrices[image_id]

"""
Function: images_in_group
Calculate and return the list of image ids in the gived group.

Parameters:
partition - the partition of the objects
group - the group who's images we need to return

Returns:
A list of images in the group.
"""
def images_in_group(partition, group):
    group_members = []
    for key, val in partition.iteritems():
        if val == group:
            group_members.append(key)
    return group_members

"""
Function: groups_in_partition
Calculate the number of groups currently being used by the partition

Parameters:
partition - the partition to count groups in

Returns:
The number of groups in the partition
"""
def groups_in_partition(partition):
    groups = []
    for key, val in partition.iteritems():
        if val not in groups:
            groups.append(val)
    return groups

"""
Function: log_prior

Calculate the log probability of a given partition of i+1 elements given the partition of i elements.

Parameters:
oldPartition - the old partitioning of the previous i elements
group - the group that the new object is being added to

Returns:
The probability of the new partition given the old
"""
def log_prior(oldPartition, group, dispersion):
    i = len(oldPartition)
    num_in_group = len(images_in_group(oldPartition, group)) + 1
    denominator = i - 1.0 + dispersion
    if num_in_group == 1:
        # this is the only image in this group
        return log(dispersion / denominator)
    else:
        return log(num_in_group / denominator)

"""
Function: discete_trunc_t_logpdf

Calulates a discrete truncated logpdf for a given set of values

Parameters:
x - array-like values to be compared
df - array-like the degrees of freedom
loc - array-like the center point of the t distribution
scale - array-like the scale of the t distribution
domain: list of the allowed values in the domain of the discrete distribution

Returns:
The log_prob for the x values
"""
def discrete_trunc_t_logpdf(x, df, domain, loc=0, scale=1):
    # make sure is numpy array
    x = array(x)

    # get the indices of the values we are interested in
    indices = empty(x.shape)
    for index, val in ndenumerate(x):
        indices[index] = domain.index(val)

    # number of elements in domain
    n = len(domain)

    # the shape for each of the values in the domain
    shape = (n,) + x.shape

    # get the values from the unmodified t over the domain
    all_log_prob = empty(shape)
    for i in range(n):
        all_log_prob[i] = t.logpdf(domain[i]*ones(x.shape), df, loc=loc, scale=scale)

    # normalize these values
    total_log_prob = logaddexp.reduce(all_log_prob, axis=0)
    norm_log_prob = all_log_prob - total_log_prob

    # get the values needed to return
    log_prob = empty(x.shape)
    for i, val in ndenumerate(x):
        # first get the index of the domain that x is at
        index = domain.index(val)

        # now get the appropriate value for the log_prob of x
        log_prob[i] = norm_log_prob[(index,)+i]

    return log_prob

"""
Function: log_likelihood

Calculates the log_likelihood of observering the set of features of the current
object given that it is from the group group_num

Parameters:
current_partition - the current partitioning of the other images
group_num - the group that the current image would be assigned to
move - the move dict holding the information about the current move
"""
def log_likelihood(current_partition, group_num, image_id, prior_mean, mean_conf, prior_var, var_conf):
    # the images grouped so far
    images = images_in_group(current_partition, group_num)

    # matrix for image
    image_matrix = get_image_matrix(image_id)

    # number of images
    n = len(images)

    if n > 0:
        # get the shape for the group
        image_shape = image_matrix.shape
        shape = (n, image_shape[0], image_shape[0])

        # get the matricies for all the images in the group
        group = empty(shape)
        for i in range(n):
            group[i] = get_image_matrix(images[i])

        # get mean, variance matrix
        group_mean = mean(group, axis=0)
        group_var = var(group, axis=0)
    else:
        group_mean = 0
        group_var = 0

    # calculate the parameters of the student_t distribution
    l = mean_conf + n
    a = var_conf + n
    mu = (mean_conf * prior_mean + n * group_mean) / l
    sig_sq = (var_conf * prior_var + (n - 1) * group_var +
              mean_conf * n * (prior_mean - group_mean) ** 2 / l) / a
    scale = sig_sq * (1 + 1 / l)

    # calculate the log probability over each dimension
    # from timing this takes about 0.09 sec
    log_p = discrete_trunc_t_logpdf(image_matrix, a, range(256), loc=mu, scale=scale)

    return sum(log_p)

"""
Function: move_probability

Calculates the probability of a given move

Parameters:
current_partition - representation of the current partition for the images.  Is a dict where each key is an image ID, and each value is the group number that image is in
move - dict of the move being made. Same form as in db

current_partition - representation of the current partition fo the images.  Is a dict where each key is an image ID, and each value is the group number that image is in
move - the move object being used in calculation

Returns:
The probability of the move
"""
def move_probability(current_partition, move, prior_mean=mu0, mean_conf=l0, prior_var=sig_sq0, var_conf=a0, dispersion=DISPERSION_PARAMETER):
    image_id = move['image_id']
    newGroup = move['new_group']
    moveProbabilities = {}
    groups = groups_in_partition(current_partition)
    if newGroup != None and newGroup not in groups:
        # if the move moves the image into a new group, add that group to groups.
        groups.append(newGroup)
    else:
        # otherwise, add the minimum val less than 8 to groups
        for i in range(8):
            if i not in groups:
                groups.append(i)
                break

    # for each of the groups in groups, calculate the probability of that one being selected
    for group in groups:
        # the probability of a given move is the likelihood times the prior given the move that happened and all prior data
        likelihood = log_likelihood(current_partition, group, image_id, prior_mean, mean_conf, prior_var, var_conf)
        prior = log_prior(current_partition, group, dispersion)
        moveProbabilities[group] = likelihood + prior

    # normalize all the probabilities properly
    total = logaddexp.reduce(moveProbabilities.values())
    for key, val in moveProbabilities.iteritems():
        moveProbabilities[key] = val - total


    return moveProbabilities

"""
Function: compare_trial
Compares the moves in a trial to the moves that a particle filter would have made

Parameters:
trial_id - the ObjectId of the trial to analyze
move_probability - a function for calculating the probability of a given move.  Takes arguments of current_partition and move, where current_partition is a dict of image_id to group number, and move is a dict for a move

Returns:
Move objects (as described in readme) augmented with move_probs, a dictionary of group-probability pairs, and partition, a dictionary of image_id-group pairs.
"""
def compare_trial(trial_id, move_probability):
    # get the trial
    trial = db.get_trial(trial_id)

    # list of the images initially currently grouped
    initial_images = [x for x in trial['init_state'] if x['group'] != -1]

    # a dict of the currently partitioned objects.  The key is the image_id, and
    # the value is the group
    current_partition = {}
    for image in initial_images:
        image_id = str(image['_id'])
        current_partition[image_id] = image['group']

    moveNum = 0
    totalMoveNum = len(trial['moves']);
    # iterate over each move in the trial
    for move in trial['moves']:
        moveNum += 1
        # calculate the normalized log probability of each potential move according to the particle filter
        if moveNum > 1:
            print "\tRunning move", moveNum, "of", totalMoveNum
            probs = move_probability(current_partition, move)

            # augment the move object
            move['move_results'] = probs
            move['partition'] = copy(current_partition)
            move['likelihood'] = probs[move['new_group']];
            print "\tFound likelihood:", move['likelihood'];
        else:
            move['move_results'] = {}
            move['partition'] = copy(current_partition)
            move['likelihood'] = 1.0;

        # update the current partition
        current_partition[move['image_id']] = move['new_group']

    return trial

"""
Function: run_all_trials
Gathers all trial ids from the database and runs them all through compare_trial, saving the results out into a file.
"""
def run_all_trials():
    # runs all the trials and writes out all data into a json string saved to results.json
    trials = db.get_all_trials()
    trialsData = {}

    # bits and pieces to let us print out something interesting
    trialNum = 0
    totalTrialNum = len(trials)
    times = []
    smallTrials = {};

    # the main loop that analyzes each trial also check time to run and whether the trial is shorter than expected
    for trial in trials:
        if len(trial['moves']) < 40:
            smallTrials[trial["_id"]] = len(trial['moves']);
        startTime = time.time()
        print "Runnning trial", trialNum, "of", totalTrialNum

        trial = compare_trial(trial["_id"], move_probability)

        endTime = time.time()
        totalTime = endTime - startTime
        print "Completed trial", trialNum, "in", totalTime, "seconds"
        print ""
        times.append(totalTime)
        trialNum += 1

    # print out some information about the calculation
    print "Done!"
    print "Average time per trial: ", sum(times)/totalTrialNum, "seconds"
    print "The following trials were smaller than expected: "
    for key, value in smallTrials.iteritems():
        print "\tTrial", key, "with", value, "moves"

    # find a results file that does not yet exist
    base = "./results"
    name = base
    number = 0
    while os.path.exists(name + ".json"):
        name = base + str(number)
        number += 1
    print "Saving results in", name, ".json"
    f = open(name + ".json", 'w')
    json.dump(trials, f)
    f.close()

"""
Function: run_all_trials_for_params
Gathers all trial ids from the database and runs them all through compare_trial, saving the results out into a file. This function finds the best parameters for each move, rather than the likelihood of the human move.

This method now runs each child through compare_trial with find_params_for_move, rather than move_probability.
"""
def run_all_trials_for_params():
    # runs all the trials and writes out all data into a json string saved to results.json
    trials = db.get_all_trials()
    trialsData = {}
    for trial in trials:
        trial = compare_trial(trial['_id'], find_params_for_move)
    # find a results file that does not yet exist
    base = "./results"
    name = base
    number = 0
    while os.path.exists(name + ".json"):
        name = base + str(number)
        number += 1
    f = open(name + ".json", 'w')
    json.dump(trials, f)
    f.close()

def run_trial_for_params(trial_id):
    trial = db.get_trial(trial_id);
    print "Starting...";
    trial = compare_trial(trial['_id'], find_params_for_move);
    print "Done!"

"""
Function: gibbs_prob
takes in a move probability, move time, and new group, and returns a probability that this set of move params is 
"""
def gibbs_prob(group, time, prob):
    maxVal = -inf
    max_group = -1
    for key, val in prob.iteritems():
        if val > maxVal:
            group = key
            maxVal = val
    if max_group != group:
        return 0
    else:
        return var(prob)

"""
Gibbs Sampling Functions

These functions sample the various parameters of our particle filter model for the gibbs sampler.
"""

def sample_mu(current_partition, move, time_elapsed, params):
    group = move['new_group'];
    # new random mu
    new_mu = truncnorm.rvs((0.0-params[0])/10.0, (255.0-params[0])/10.0, params[0], 10.0) # pretty random...
    # sample both probs
    mu_log_prob = move_probability(current_partition, move, params[0], params[1], params[2], params[3], params[4])[group]
    new_mu_log_prob = move_probability(current_partition, move, new_mu, params[1], params[2], params[3], params[4])[group]
    diff = exp(new_mu_log_prob - mu_log_prob)
    # choose one
    prob = mu_log_prob
    if diff >= 1.0 or random.uniform(0.0, 1.0) <= diff:
        params[0] = new_mu
        prob = new_mu_log_prob
    return [params, prob]

def sample_mu_conf(current_partition, move, time_elapsed, params):
    group = move['new_group'];
    # new random mu_conf
    new_mu_conf = truncnorm.rvs((-500.0-params[1])/4.0, (500.0-params[1])/4.0, params[1], 4.0) # pretty random...
    # sample both probs
    mu_conf_log_prob = move_probability(current_partition, move, params[0], params[1], params[2], params[3], params[4])[group]
    new_mu_conf_log_prob = move_probability(current_partition, move, params[0], new_mu_conf, params[2], params[3], params[4])[group]
    diff = exp(new_mu_conf_log_prob - mu_conf_log_prob)
    # choose one
    prob = mu_conf_log_prob
    if diff >= 1.0 or random.uniform(0.0, 1.0) <= diff:
        params[1] = new_mu_conf
        prob = new_mu_conf_log_prob
    return [params, prob]

def sample_var(current_partition, move, time_elapsed, params):
    group = move['new_group'];
    # new random var
    new_var = truncnorm.rvs((0.0-params[2])/8.0, (256.0*256.0-params[2])/8.0, params[1], 8.0) # pretty random...
    # sample both probs
    var_log_prob = move_probability(current_partition, move, params[0], params[1], params[2], params[3], params[4])[group]
    new_var_log_prob = move_probability(current_partition, move, params[0], params[1], new_var, params[3], params[4])[group]
    diff = exp(new_var_log_prob - var_log_prob)
    # choose one
    prob = var_log_prob
    if diff >= 1.0 or random.uniform(0.0, 1.0) <= diff:
        params[2] = new_var
        prob = new_var_log_prob
    return [params, prob]

def sample_var_conf(current_partition, move, time_elapsed, params):
    group = move['new_group'];
    # new random var_conf
    new_var_conf = truncnorm.rvs((-500.0-params[3])/4.0, (500.0-params[3])/4.0, params[3], 4.0) # pretty random...
    # sample both probs
    var_conf_log_prob = move_probability(current_partition, move, params[0], params[1], params[2], params[3], params[4])[group]
    new_var_conf_log_prob = move_probability(current_partition, move, params[0], params[1], params[2], new_var_conf, params[4])[group]
    diff = exp(new_var_conf_log_prob - var_conf_log_prob)
    # choose one
    prob = var_conf_log_prob
    if diff >= 1.0 or random.uniform(0.0, 1.0) <= diff:
        params[3] = new_var_conf
        prob = new_var_conf_log_prob
    return params, prob

def sample_disp(current_partition, move, time_elapsed, params):
    group = move['new_group'];
    # new random disp
    new_disp = truncnorm.rvs((0.0-params[4])/4.0, (1000.0-params[4])/4.0, params[4], 4.0) # pretty random...
    # sample both probs
    disp_log_prob = move_probability(current_partition, move, params[0], params[1], params[2], params[3], params[4])[group]
    new_disp_log_prob = move_probability(current_partition, move, params[0], params[1], params[2], params[3], new_disp)[group]
    diff = exp(new_disp_log_prob - disp_log_prob)
    # choose one
    prob = disp_log_prob
    if diff >= 1.0 or random.uniform(0.0, 1.0) <= diff:
        params[4] = new_disp
        prob = new_disp_log_prob
    return [params, prob]

"""
Function: find_params_for_move
Runs gibbs over the variables in our particle filter, attempting to find the ideal parameters for a given human move.d

Variables to Sample:
mu - mean - >= 0, <= 255
mu_conf - confidence in prior mean -
var - variance - >= 0, <=
var_conf - confidence in prior variance - 
dispersion - dispersion parameter to dirichlet - > 0

All moves are made via a random sample from a normal distribution

Parameters:
current_partition - the current partition of the images into groups
move - the move object being used in this calculation

Returns:
The mean of the samples taken
"""
def find_params_for_move(current_partition, move):
    # first generate a random start point
    mu = random.normal(255.0/2.0, 256.0/4.0)
    mu_conf = random.uniform(0.0, 100.0)
    sig = random.normal((255.0/4.0) ** 0.5, ((255.0/4.0) ** 0.5)/8.0) # pretty arbitrary normal dist params
    var_conf = random.uniform(0.0, 100.0)
    disp = random.normal(50.0, 25.0) # another pretty arbitrary distribution

    params = [mu, mu_conf, sig, var_conf, disp]
    sample_params = []

    image_id = move['image_id']
    group = move['new_group']
    time_elapsed = move['time_elapsed']
    print "Starting with sample:", str(params)

    # iterate across the variables, testing each new suggestion in turn
    print "Walking in...."
    for i in range(walk_in):
        # sample mu
        params, prob = sample_mu(current_partition, move, time_elapsed, params)
        print("4")
        print "\tresulting prob:", str(prob)
        # sample mu_conf
        params, prob = sample_mu_conf(current_partition, move, time_elapsed, params)
        print("3")
        print "\tresulting prob:", str(prob)
        # sample var
        params, prob = sample_var(current_partition, move, time_elapsed, params)
        print("2")
        print "\tresulting prob:", str(prob)
        # sample var_conf
        params, prob = sample_var_conf(current_partition, move, time_elapsed, params)
        print("1")
        print "\tresulting prob:", str(prob)
        # sample disp
        params, prob = sample_disp(current_partition, move, time_elapsed, params)
        print "\tWalk in sample:", str(params)
        print "\tresulting prob:", str(prob)

    print "Sampling..."
    for j in range(samples):
        # sample mu
        params, prob = sample_mu(current_partition, move, time_elapsed, params)
        print("4")
        # sample mu_conf
        params, prob = sample_mu_conf(current_partition, move, time_elapsed, params)
        print("3")
        # sample var
        params, prob = sample_var(current_partition, move, time_elapsed, params)
        print("2")
        # sample var_conf
        params, prob = sample_var_conf(current_partition, move, time_elapsed, params)
        print("1")
        # sample disp
        params, prob = sample_disp(current_partition, move, time_elapsed, params)
        print "\tNew sample:", str(params)
        print "\tresulting prob:", str(prob)

        # save the sample we just generated
        sample_params.append(params[:])

    print "Move of image " + str(image_id) + " to group " + str(group) + " found params: " + str(params)
    print "Resulting probability is " + str(move_probability(current_partition, move, params[0], params[1], params[2], params[3], params[4]))
    print "mean is " + str(mean(array(sample_params), axis=0))
    return mean(array(sample_params), axis=0)

"""
Function: randomize
Randomize the list by permuting in place. Knuth's algorithm

Parameters:
l - the list to randomize
"""
def randomize(l):
    for i in range(len(l) - 1, -1, -1):
        randIndex = int(floor(random.uniform(0, i+1)))
        switchElem = l[randIndex]
        otherElem = l[i]
        l[randIndex] = otherElem
        l[i] = switchElem

"""
Function: decide_group
Given an image and a partition, decides with group to add the image to.

Parameters:
partition - the exisiting partition of the data
image_id - the id of the image that is going to be added

Returns:
The group to add the image to.
"""
def decide_group(partition, image_id):
    probabilities = move_probability(partition, image_id)
    print 'Probabilities:', probabilities
    maxVal = -inf
    group = -1
    for key, val in probabilities.iteritems():
        if val > maxVal:
            group = key
            maxVal = val
    return (probabilities, group)

"""
Function: sort_image_set
Returns a sorted set of image groups given sort_image_set. This is a sanity checker for the main job of analysis: analyzing all the sample human data we have gathered.

Parameters:
set_id - the id of the image set to sort
"""
def sort_image_set(set_id):
    # get the image set
    image_set = db.get_image_set(set_id)

    # get everything from the images field
    images = image_set['images']

    # randomize images
    randomize(images)

    # for each image in the list, run it through the algoritm
    partition = {}
    probs = {}
    for image in images:
        image_id = str(image['image_id'])
        probs, group = decide_group(partition, image_id)
        print "Adding image to group " + str(group)
        partition[image_id] = group
        probs[image_id] = probs
    return (probs, partition)

"""
Function: sort_and_print_set
Prints out the groupings of the images in the set given by the provided id

Parameters:
set_id - the id of the image set to sort
"""
def sort_and_print_set(set_id=None):
    if set_id == None:
        # choose a set
        image_sets = db.get_all_image_sets()
        set_id = image_sets[0]['_id']

    print "Sorting image set with id " + str(set_id)

    # partition it
    (probs, partition) = sort_image_set(set_id)
    print "Image set sorted"

    # save the results to disk
    base = "./sort"
    name = base
    number = 0
    while os.path.exists(name) or os.path.exists(name + ".txt"):
        name = base + str(number)
        number += 1

    # print the results
    os.makedirs(name + "/")
    f = open(name + ".txt", 'w')
    f.write("SORT\n")
    groups = groups_in_partition(partition)
    for group in groups:
        print "Group " + str(group) + ":"
        f.write("Group " + str(group) + ":\n")
        group_images = images_in_group(partition, group)
        i = 0

        for image in group_images:
            fileName = name + "/" + str(group) + "-" + str(i) + ".png"
            imageObj = Image.open(db.get_image_file(image))
            imageObj.save(fileName, "PNG")
            print "\t" + fileName
            f.write("\t" + fileName + "\n")
            i += 1
    print "DONE"
    f.write("DONE\n")
    f.close()
