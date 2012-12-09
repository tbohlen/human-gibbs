"""
Flask server
"""
from flask import Flask
from flask import render_template
from flask import request
import db
import json

app = Flask(__name__)

@app.route("/")
def hello():
    return render_template("index.html", hello=True);

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
