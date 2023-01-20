import os
import time
from datetime import datetime

from flask import Flask, request, abort, jsonify, send_from_directory, flash, redirect, url_for
from werkzeug.utils import secure_filename

from multiprocessing import Pool, Process
import threading
import json
from model import recommend
from flask_cors import CORS
import shutil
from fast_autocomplete import AutoComplete

db = {}
with open('Output/proposals_titles_db.json', 'r') as f:
    db = json.load(f)
autocomplete = AutoComplete(words=db)

# FILES_DIRECTORY = "/usr/src/app/files/"
FILES_DIRECTORY = "./files/"
DB_DIRECTORY = "./Output/"

if not os.path.exists(FILES_DIRECTORY):
    os.mkdir(FILES_DIRECTORY)
        
api = Flask(__name__)
CORS(api)
api.config['FILES_DIRECTORY'] = FILES_DIRECTORY
api.config['DB_DIRECTORY'] = DB_DIRECTORY

@api.route('/test/', methods=['GET'])
def test():
    return "hi"

@api.route('/suggest/<user_input>/', methods=['GET'])
def suggest(user_input):
    relevant_titles = autocomplete.search(word=user_input, max_cost=10, size=10)
    suggestions = []
    for relevant_title in relevant_titles:
        rel_title = relevant_title[0]
        suggestion = {}
        suggestion['title'] = rel_title
        suggestion.update(db[rel_title])
        suggestions.append(suggestion)
    return jsonify(suggestions)

@api.route('/recommend_scholars/<pid>/<agency>/<top_k>/', methods=['GET'])
def recommend_scholars(pid,agency,top_k):
    if request.method == 'GET':
        if top_k == '':
            top_k = 20
        else:
            top_k = int(top_k)
        
        searchfile = str(pid) + '_' + str(top_k) + '.json'
        files_path = api.config['FILES_DIRECTORY']
        
        if not os.path.exists(files_path):
            os.mkdir(files_path)
            
        db_path = api.config['DB_DIRECTORY']
        if searchfile in os.listdir(files_path):
            searchfilepath = files_path + searchfile
            f = open(searchfilepath)
            scholars = json.load(f)
            return jsonify(scholars)
        else:
            config_file = './config.yml'
            output_file = "/files/" + str(pid) + '_' + str(top_k)
            proposal_id = pid
            generator = 'Spacy'
            cpu_count = 40
            r = recommend(config_file,top_k,proposal_id,generator,cpu_count,agency,db_path,output_file)
            
            searchfilepath = files_path + searchfile
            f = open(searchfilepath)
            scholars = json.load(f)
            return jsonify(scholars)
        
        return pid+","+agency+","+top_k
    else:
        return "Not Allowed"

if __name__ == "__main__":
    api.run(debug=True, port=9000)