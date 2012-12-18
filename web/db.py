from bson.objectid import ObjectId
from bson.dbref import DBRef
from gridfs import GridFS
from os import listdir, makedirs
from os.path import isfile, join, splitext, basename, exists
from mimetypes import guess_type, guess_extension
from numpy.random import randint
import os
import pymongo
from urlparse import urlparse

MONGO_URL = os.environ.get('MONGOHQ_URL')

# connect to mongo
if MONGO_URL:
    # Get a connection
    conn = pymongo.Connection(MONGO_URL)
    
    # Get the database
    db = conn[urlparse(MONGO_URL).path[1:]]
else:
    # Not on an app with the MongoHQ add-on, do some localhost action
    conn = pymongo.Connection('localhost', 27017)
    db = conn['human-gibbs']

# connect gridFS
fs = GridFS(db)

### Adding and reading image ###

# check if a path referes to an image file
def is_image(file_path):
    image_extensions = ['.jpg','.png','.jpeg', '.jpe', '.gif']
    file_name, file_ext = splitext(file_path)
    return isfile(file_path) and file_ext in image_extensions

# adds an image set. Uses the directory name for the folder path. Returns the
# objectId for the image document
#
# The uses of ValueError and TypeError are stretches for their defined purpose,
# but using different errors allows us to detect what went wrong in imageGen
def add_image_set_by_array(images, parents, name):
    # check for duplicate name
    if db.images.find_one({'name': name}) != None:
        raise ValueError(('An image set with the name %s already exists. Please ' +
                         'change the folder name and try uploading again.') % name)

    # put all the parent images into gridFS, save their object IDs
    parent_list = []
    for image in parents:
        with open(image, 'rb') as f:
            data = f.read()
            content_type = guess_type(image)[0]
            if content_type == None:
                raise TypeError(('Couldn\'t guess the file extension for %s. ' +
                                 'Check the filename.') % image)
            parent_id = fs.put(data, content_type=content_type)
            parent_list.append(parent_id)

    # put all the images into gridFS, save their object IDs
    image_list = []
    for image in images:
        with open(image['path'], 'rb') as f:
            data = f.read()
            content_type = guess_type(image['path'])[0]
            if content_type == None:
                raise TypeError(('Couldn\'t guess the file extension for %s. ' +
                                 'Check the filename.') % image['path'])
            image_id = fs.put(data, content_type=content_type)
            image_list.append({'image_id': image_id, 'parent': parent_list[image['category']], 'category': image['category']})

    # save the image set, return the 
    return db.images.insert({'name': name,
                             'parents': parent_list,
                             'images': image_list})

# adds an image set. Uses the directory name for the folder path. Returns the
# objectId for the image document
def add_image_set(dir_path, name=None):
    # get all the images
    paths = [join(dir_path, f) for f in listdir(dir_path)] # get full paths
    images = filter(is_image, paths) # keep only image files

    # get name for set from folder name
    if name == None:
        name = basename(dir_path)
    if db.images.find_one({'name': name}) != None:
        raise ValueError(('An image set with the name %s already exists. Please ' +
                         'change the folder name and try uploading again.') % name)

    # put all the images into gridFS, save their object IDs
    image_list = []
    for image in images:
        with open(image, 'rb') as f:
            data = f.read()
            content_type = guess_type(image)[0]
            if content_type == None:
                raise TypeError(('Couldn\'t guess the file extension for %s. ' +
                                 'Check the filename.') % image)
            image_id = fs.put(data, content_type=content_type)
            image_list.append({'image_id': image_id})

    # save the image set, return the 
    return db.images.insert({'name': name,
                             'images': image_list})

# takes the trial_id as a string and returns the image set        
def get_image_set(trial_id):
    trial = db.trials.find_one({'_id': ObjectId(trial_id)})
    return db.dereference(trial['image_set'])

# gets a list of all names in the image set
def image_names(image_set):
    # write image set to the directory
    image_names = []
    i = 0 # index for filenames
    for image_map in image_set['images']:
        # find the image
        image = fs.get(image_map['image_id'])

        # choose the filename
        ext = guess_extension(image.content_type)
        name = str(i) + ext

        # add the filename to the list
        image_names.append(name)

        # inc i
        i += 1

    return image_names

# writes all the images in an image set to a desired folder location
def write_image_set(image_set_name, target_dir):
    # make sure directory exists
    if not exists(target_dir):
        makedirs(target_dir)
    
    # find image set
    image_set = db.images.find_one({'name': image_set_name})

    # get a list of filenames
    filenames = [join(target_dir, x) for x in image_names(image_set)]

    for i in range(len(filenames)):
        image = fs.get(image_set['images'][i]['image_id'])
        
        with open(filenames[i], 'wb') as f:
            f.write(image.read())

def get_image_file(image_id):
    # get the image
    return fs.get(ObjectId(image_id))

# returns a list of all image sets
def get_all_image_sets():
    # list of image sets
    image_sets = []
    
    # get a cursor over the sets
    set_cursor = db.images.find()

    # add all image_sets
    for i in range(set_cursor.count()):
        image_sets.append(set_cursor[i])
        
    return image_sets

# return a specific image set
def get_image_set(set_id):
    return db.images.find_one({'_id': ObjectId(set_id)})

### Adding and getting trials ###
    
# add a trial to the system, returns string of the ID for the trial. 
def add_trial(init_state, image_set, tester):
    trial_id = db.trials.insert({'init_state': init_state,
                                 'moves': [],
                                 'image_set': DBRef('images', image_set['_id']),
                                 'tester': tester})
    return str(trial_id)

# adds a trial based off a random image set from the database. All images are
# assumed to not start on the board, i.e., all images are unstaged
def add_unstaged_trial(tester):
    # get a cursor over the image sets
    image_sets = db.images.find()

    # choose a random image set
    num_sets = image_sets.count()
    image_set = image_sets[randint(num_sets)]
    
    # add all the images to the trial
    init_state = []
    for image in image_set['images']:
        init_state.append({'image_id': image['image_id'],
                           'group': -1,
                           'x': -1,
                           'y': -1})

    return add_trial(init_state, image_set, tester)

def get_trial(trial_id):
    return db.trials.find_one({'_id': ObjectId(trial_id)})

def get_all_trials():
    # return all the trials in the database
    trials_cursor = db.trials.find()
    trials = []

    for i in range(trials_cursor.count()):
        trials.append(trials_cursor[i])

    return trials

### Adding moves ###

# add a move to a trial. Takes the trial ID as a string
def add_move(trial_id, move):
    return db.trials.update({'_id': ObjectId(trial_id)},
                            {'$push': {'moves': move}})

# checks a dict representing a move to make sure it has all the required fields
def has_move_fields(move):
    move_fields = ['image_id', 'old_group', 'new_group', 'old_x', 'new_x',
                   'old_y', 'new_y', 'time_elapsed']

    # make sure each field is in the dict
    for field in move_fields:
        if field not in move:
            return False

    # if here, it must have all the fields
    return True
