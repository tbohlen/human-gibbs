#! /usr/bin/python

"""
Flask server
"""
from flask import Flask, render_template, request, make_response, send_file
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
    resp = make_response(render_template("index.html", hello=True))

    # create a new trail, get the id
    trial_id = db.add_unstaged_trial() # TODO: choose actual set somehow

    # store the ID as a cookie and return the generated HTML
    resp.set_cookie('trial_id', trial_id)
    return resp

@app.route("/move", methods=['POST'])
def move():
    # get trial id
    trial_id = request.cookies.get('trial_id')

    try:
        # get the move data from the form.  If it isn't there, fails
        move = json.loads(request.form['move'])

        # make sure the move has all the necessary fields
        if not db.has_move_fields(move):
            return "Move missing some of the required fields. Check the README to see which"

        # add the move data to the database
        db.add_move(trial_id, move)
        return "Success!"
    except KeyError:
        return "Must have value for move key in form data!"

@app.route("/images")
def images():
    # get trial id
    trial_id = request.cookies.get('trial_id')
    
    # get a list of image names
    image_names = db.image_names(db.get_image_set(trial_id))

    image_urls = ['/images/' + str(i) for i in range(len(image_names))]

    return json.dumps(image_urls)

@app.route("/images/<int:image_num>")
def image(image_num):
    # get trial id
    trial_id = request.cookies.get('trial_id')

    # get the image
    image = db.get_image_file(trial_id, image_num)

    return send_file(image, mimetype=image.content_type, cache_timeout=0)

if __name__ == "__main__":
    app.run()
