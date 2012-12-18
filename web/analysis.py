import db
import imageGen
from numpy import *
from scipy.stats import t

mu0 = 255 / 256.0 # prior mean
l0 = 1 # confidence in prior mean
sig_sq0 = (256 / 4.0)**2 # prior variance
a0 = 1 # confidence in prior variance

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
Function: log_likelihood

Calculates the log_likelihood of observering the set of features of the current
object given that it is from the group group_num

Parameters:
current_partition - the current partitioning of the other images
group_num - the group that the current image would be assigned to
move - the move dict holding the information about the current move
"""
def log_likelihood(current_partition, group_num, move):
    # the images grouped so far
    images = images_in_group(current_partition, group_num)

    # number of images
    n = len(images)

    # matrix for image
    image_matrix = get_image_matrix(move['image_id'])

    # get the shape for the group
    image_shape = image_matrix.shape
    shape = (n, image_shape[0], image_shape[0])
    
    # get the matricies for all the images in the group
    group = empty(shape)
    for i in range(n):
        group[i] = get_image_matrix(images[i])

    # calculate parameters common to all dimensions
    l = l0 + n
    a = a0 + n

    # get mean, variance matrix
    group_mean = mean(group, axis=0)
    group_var = var(group, axis=0)

    # calculate the parameters of the student_t distribution
    mu = (l0 * mu0 + n * group_mean) / l
    sig_sq = (a0 * sig_sq0 + (n - 1) * group_var +
              l0 * n * (mu0 - group_mean) ** 2 / l) / a
    scale = sig_sq * (1 + 1 / l)

    # calculate the log probability over each dimension
    log_p = t.logpdf(image, a, loc=mu, scale=scale)

    return sum(log_p)
    
"""
Function: move_probability

Calculates the probability of a given move

Parameters:
current_partition - representation of the current partition for the images.  Is a dict where each key is an image ID, and each value is the group number that image is in
move - dict of the move being made. Same form as in db

Returns:
The probability of the move
"""
def move_probability(current_partition, move):
    pass

"""
Function: compare_trial
Compares the moves in a trial to the moves that a particle filter would have made

Parameters:
trial_id - the ObjectId of the trial to analyze
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
