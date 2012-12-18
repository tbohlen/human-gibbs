import db
import imageGen
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
Function: prior_probability

Calculate the probability of a given partition of i+1 elements given the partition of i elements.

Parameters:
oldPartition - the old partitioning of the previous i elements
group - the group that the new object is being added to

Returns:
The probability of the new partition given the old
"""
def prior_probability(oldPartition, group):
    i = len(oldPartition)
    num_in_group = len(images_in_group(oldPartition, group)) + 1
    denominator = i - 1.0 + DISPERSION_PARAMETER
    if num_in_group == 1:
        # this is the only image in this group
        return DISPERSION_PARAMETER / denominator
    else:
        return num_in_group / denominator

"""
Function: move_probability

Calculates the probability of a given move

Parameters:
current_partition - representation of the current partition fo the images.  Is a dict where each key is an image ID, and each value is the group number that image is in
move - dict of the move being made. Same form as in db
"""
def move_probability(current_partition, move):
    pass

"""
Function: compare_trial
Compares the moves in a trial to the moves that a particle filter would have made

Parameters:
trial_id - the ObjectId of the trial to analyze
image_set_matricies - a dict of matrices corresponding to an image set. Should be the output of get_image_set_matrices()
move_probability - a function for calculating the probability of a given move.  Takes arguments of current_partition and move, where current_partition is a dict of image_id to group number, and move is a dict for a move

Returns:
A list of move probabilities, i.e. a list of the probabilities of each move done by the person in the trial.
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

    # a list of the probabilities of each move that the human made in the trial,
    # according to the particle fliter
    prob_of_moves = []

    # iterate over each move in the trial
    for move in moves:
        # calculate the probability of the move according to the particle filter
        p = move_probability(current_partition, move)

        # appends the probability of the move to the list of probabilities
        prob_of_moves.append(p)

        # update the current partition
        current_partition[move['image_id']] = move['new_group']

    return prob_of_moves
