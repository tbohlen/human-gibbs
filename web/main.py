"""
Flask server
"""
from flask import Flask
from flask import render_template
app = Flask(__name__)

@app.route("/")
def hello():
    return render_template("index.html", hello=True);

if __name__ == "__main__":
    app.run()
