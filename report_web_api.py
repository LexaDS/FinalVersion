import flask
from flask import request, jsonify,render_template
import os
from os import path


app = flask.Flask(__name__)
app.config["DEBUG"] = True

@app.route('/', methods=['GET'])
def home():
    return '''<h1>My project page</p>'''

@app.route('/summary', methods=['POST','GET'])
def api_post():
    if not request.json or not 'title' in request.json:
        print('400')
    file_path=path.realpath("/home/lexa/Report/JitDifferencesBetween20.8.56.391962and20.8.65.393033Summary.txt")
    with open(file_path,"r+") as f:
        return render_template('txt.html', text=f.read())

app.run(host=os.getenv('IP', '0.0.0.0'),port=int(os.getenv('PORT', 4444)))