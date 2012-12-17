import db
import imageGen
from numpy import *


"""
Function: get_image_set_matrices

Converts image_ids into the matrices representing each image.

Returns:
Dict of of the following form:
{image_set_id: {image_id: numpy.ndarray}}
where the numpy.ndarray is the numpy array of the bits in the image matrix

"""
def get_image_set_matrices():
    image_sets = {}
    
    # list of all image sets
    image_sets_list = db.get_all_image_sets()

    for image_set in image_sets_list:
        # get a dict over all matrices
        matrices = {}
        for image in image_set['images']:
            img_id = str(image['image_id'])
            image_file = db.get_image_file(img_id)
            matrices[img_id] = array(imageGen.loadImage(image_file))
            
        # add image set to list
        image_sets[str(image_set['_id'])] = matrices

    return image_sets

"""
Function: move_probability

Calculates the probability of a given move

Parameters:
current_partition - representation of the current partition fo the images.  Is a dict where each key is an image ID, and each value is the group number that image is in
move - dict of the move being made
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

def compare_trial(trial_id, image_set_matrices, move_probability):
    # get the trial
    trial = db.get_trial(trial_id)

    # the the id of the image set
    image_set_id = str(trial['image_set'].id)

    # get the image matrices
    image_matrices = image_set_matrices[image_set_id]

    # adds the matrix representing an image to a dict with an
    # 'image_id' key. 
    def add_matrix(image_dict):
        image_id = str(image_dict['image_id'])
        image_dict['matrix'] = image_matrices[image_id]
        return image_dict

    # list of the images initially currently grouped
    initial_images = [x in trial['init_state'] if x['group'] != -1]

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
        # add a key for the image matrix to the move
        move = add_matrix(move)
        
        # calculate the probability of the move according to the particle filter
        p = move_probability(current_partition, move)

        # appends the probability of the move to the list of probabilities
        prob_of_moves.append(p)

        # update the current partition
        current_partition[move['image_id']] = move['new_group']

    return prob_of_moves


