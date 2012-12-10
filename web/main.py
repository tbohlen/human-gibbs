"""
Flask server
"""
from flask import Flask, render_template, request, make_response
import db
import json

app = Flask(__name__)
app.config['DEBUG'] = True

@app.route("/")
def hello():
    # generate the HTML for the trial
    resp = make_response(render_template("index.html", hello=True))

    # create a new trail, get the id
    trial_id = db.add_unstaged_trial('kittens') # TODO: choose actual set somehow

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

@app.route("/data/trials", methods='GET')
def trials():
    return "Conversion from Mongo to JSON not implemented yet!"

@app.route("/data/trials/<int:trial_id>/moves", methods=['POST','GET'])
def moves(trial_id):
    if request.method == 'POST':
        try:
            move = json.loads(request.form['move'])
            if not has_move_fields(move):
                return "Move missing some of the required fields. Check the README to see which"
            db.add_move(trial_id, request.form['move'])
        except KeyError:
            return "Must have value for move key in form data!"
            
    else:
        return "Conversion from Mongo to JSON not implemented yet!"

if __name__ == "__main__":
    app.run()
