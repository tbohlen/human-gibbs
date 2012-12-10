from pymongo import MongoClient
from bson.objectid import ObjectId
from bson.dbref import DBRef
from gridfs import GridFS
from os import listdir, makedirs
from os.path import isfile, join, splitext, basename, exists
from mimetypes import guess_type, guess_extension

# connect to the mongo cdatabase and gridFS
connection = MongoClient()
db = connection['human-gibbs']
fs = GridFS(db)

# check if a path referes to an image file
def is_image(file_path):
    image_extensions = ['.jpg','.png','.jpeg', '.jpe', '.gif']
    file_name, file_ext = splitext(file_path)
    return isfile(file_path) and file_ext in image_extensions

# adds an image set. Uses the directory name for the folder path. Returns the
# objectId for the image document
def add_image_set(dir_path):
    # get all the images
    paths = [join(dir_path, f) for f in listdir(dir_path)] # get full paths
    images = filter(is_image, paths) # keep only image files

    # get name for set from folder name
    name = basename(dir_path)
    if db.images.find_one({'name': name}) != None:
        raise Exception(('An image set with the name %s already exists. Please ' +
                         'change the folder name and try uploading again.') % name)

    # put all the images into gridFS, save their object IDs
    image_ids = []
    for image in images:
        with open(image, 'rb') as f:
            data = f.read()
            content_type = guess_type(image)[0]
            if content_type == None:
                raise Exception(('Couldn\'t guess the file extension for %s. ' +
                                 'Check the filename.') % image)
            image_id = fs.put(data, content_type=content_type)
            image_ids.append(image_id)

    # save the image set, return the 
    return db.images.insert({'name': name,
                             'image_ids': image_ids})

# writes all the images in an image set to a desired folder location
def write_image_set(image_set_name, target_dir):
    # make sure directory exists
    if not exists(target_dir):
        makedirs(target_dir)
    
    # find image set
    image_set = db.images.find_one({'name': image_set_name})

    # write image set to the directory
    i = 0 # index for filenames
    for image_id in image_set['image_ids']:
        # find the image
        image = fs.get(image_id)

        # choose the filename
        ext = guess_extension(image.content_type)
        name = join(target_dir, str(i) + ext)

        # write the image file
        with open(name, 'wb') as f:
            f.write(image.read())
        i += 1
    
# add a trial to the system, returns string of the ID for the trial. 
def add_trial(init_state, image_set_name):
    image_set = db.images.find_one({'name': image_set_name})
    trial_id = db.trials.insert({'init_state': init_state,
                                 'moves': [],
                                 'image_set': DBRef('images', image_set['_id'])})
    return str(trial_id)

# adds a trial based off an image set. All images are assumed to not start on
# the board, i.e., all images are unstages
def add_unstaged_trial(image_set_name):
    image_set = db.images.find_one({'name': image_set_name})    
    num_images = len(image_set['image_ids'])
    init_state = []
    for i in range(num_images):
        init_state.append({'id': i,
                           'group': -1,
                           'x': -1,
                           'y': -1})

    return add_trial(init_state, image_set_name)

# add a move to a trial. Takes the trial ID as a string
def add_move(trial_id, move):
    return db.trials.update({'_id': ObjectId(trial_id)},
                            {'$push': {'moves': move}})

# checks a dict representing a move to make sure it has all the required fields
def has_move_fields(move):
    move_fields = ['id', 'old_group', 'new_group', 'old_x', 'new_x',
                   'old_y', 'new_y', 'time_elapsed']

    # make sure each field is in the dict
    for field in move_fields:
        if field not in move:
            return False

    # if here, it must have all the fields
    return True
