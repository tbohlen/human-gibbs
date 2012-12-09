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
    
# add a trial to the system, returns the ID for the trial. 
def add_trial(init_state, image_set_name):
    image_set = db.images.find_one({'name': image_set_name})
    return db.trials.insert({'init_state': init_state,
                             'moves': [],
                             'image_set': DBRef('images', image_set['_id'])})

# add a move to a trial. Takes the trial ID as a string
def add_move(trial_id, move):
    db.trials.update({'_id': ObjectId(trial_id)},
                     {'$push': {'moves': move}})
