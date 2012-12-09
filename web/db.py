from pymongo import MongoClient
from bson.objectid import ObjectId

# connect to the mongo collection
connection = MongoClient()
db = connection['human-gibbs']
trials = db.trials

# add a trial to the system, returns the ID for the trial
def add_trial(init_state):
    trial_id = trials.insert({'init_state': init_state,
                              'moves': []})
    return str(trial_id)

# add a move to a trial. Takes the trial ID as a string
def add_move(trial_id, move):
    trials.update({'_id': ObjectId(trial_id)},
                  {'$push': {'moves': move}})
