#! /usr/bin/python

"""
Flask server
"""
from flask import Flask, render_template, request, make_response, send_file, redirect
import db
import json

app = Flask(__name__)
app.config['DEBUG'] = True

# if in DEBUG mode, set static resources to expire immediately
if app.config['DEBUG']:
    app.get_send_file_max_age = lambda x: 0

@app.route("/")
def start():
    # generate the HTML for the trial
    resp = make_response(render_template("instructions.html"))
    return resp

def initialize_trial(name):
    """ Takes the name of the user taking the trial, initializes
    a trial, adds a cookie with the trial id to the response, and
    returns the response"""
    # initialize a new trial
    trial_id = db.add_unstaged_trial(name)

    # generate the response
    resp = redirect('/sorter')

    # save the trial cookie
    resp.set_cookie('trial_id', trial_id)

    # return the response
    return resp

@app.route("/turker", methods=['GET','POST'])
def turker():
    if request.method == 'GET':
        return render_template("turker-instructions.html")
    else:
        return initialize_trial("Mechanical Turker")

@app.route("/friend", methods=['GET','POST'])
def friend():
    if request.method == 'GET':
        return render_template("friend-instructions.html")
    else:
        return initialize_trial(request.form['name'])

@app.route("/sorter")
def storter():
    if request.cookies.get('trial_id'):
        return render_template("index.html")
    else:
        return "Must come to sorter after registering as a friend or through mechanical turk", 500

@app.route("/move", methods=['POST'])
def move():
    # get trial id
    trial_id = request.cookies.get('trial_id')

    try:
        # get the move data from the form.  If it isn't there, fails
        move = json.loads(request.form['move'])

        # make sure the move has all the necessary fields
        if not db.has_move_fields(move):
            return "Move missing some of the required fields. Check the README to see which", 500

        # add the move data to the database
        try:
            return str(db.add_move(trial_id, move))
        except e:
            return str(e), 500
    except KeyError:
        return "Must have value for move key in form data!", 500

@app.route("/images")
def images():
    # get trial id
    trial_id = request.cookies.get('trial_id')
    
    # get the trials image set
    image_set = db.get_image_set(trial_id)

    image_ids = [str(image['image_id']) for image in image_set['images']]

    return json.dumps(image_ids)

@app.route("/images/<image_id>")
def image(image_id):
    # get the image
    image = db.get_image_file(image_id)

    return send_file(image, mimetype=image.content_type, cache_timeout=0)

@app.route("/trial-id")
def trial_id():
    # return the trial id
    return json.dumps(request.cookies.get('trial_id'))

if __name__ == "__main__":
    app.run(host='0.0.0.0')
