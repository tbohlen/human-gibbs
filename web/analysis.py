import db
import imageGen
import json
from numpy import *

DISPERSION_PARAMETER = 10.0

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

Calculate the probability of a given partition of i+1 elements given the partition of i elements.

Parameters:
oldPartition - the old partitioning of the previous i elements
group - the group that the new object is being added to

Returns:
The probability of the new partition given the old
"""
def log_prior(oldPartition, group):
    i = len(oldPartition)
    num_in_group = len(images_in_group(oldPartition, group)) + 1
    denominator = i - 1.0 + DISPERSION_PARAMETER
    if num_in_group == 1:
        # this is the only image in this group
        return log(DISPERSION_PARAMETER / denominator)
    else:
        return log(num_in_group / denominator)

"""
Function: move_probability

Calculates the probability of a given move

Parameters:
current_partition - representation of the current partition fo the images.  Is a dict where each key is an image ID, and each value is the group number that image is in
move - dict of the move being made. Same form as in db
"""
def move_probability(current_partition, move):
    moveProbabilities = {}
    groups = groups_in_partition(current_partition)
    if move.group not in groups:
        # if the move moves the image into a new group, add that group to groups.
        groups.append(move.group)
    else:
        # otherwise, add the minimum val less than 8 to groups
        for i in range(8):
            if i not in groups:
                groups.append(i)
                break

    # for each of the groups in groups, calculate the probability of that one being selected
    for group in groups:
        # the probability of a given move is the likelihood times the prior given the move that happened and all prior data
        likelihood = log_likelihood(current_partition, group, move)
        prior = prior_probability(current_partition, group)
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
image_set_matricies - a dict of matrices corresponding to an image set. Should be the output of get_image_set_matrices()
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

    # iterate over each move in the trial
    for move in trial['moves']:
        # calculate the normalized log probability of each potential move according to the particle filter
        probs = move_probability(current_partition, move)

        # augment the move object
        move['move_probs'] = probs
        move['partition'] = copy(current_partition)

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
    for trial in trials:
        trial = compare_trial(trial._id, move_probability)
    # find a results file that does not yet exist
    base = "./results"
    name = base
    number = 0
    while os.path.exists(name + ".json"):
        name = base + str(number)
        number += 1
    f = open(name + ".json")
    json.dump(trials, f)
    f.close()

