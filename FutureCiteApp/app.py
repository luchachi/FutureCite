from flask import Flask, render_template, request, jsonify
from src.access_api import process_abstract
import random
import os

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/check_api_key')
def check_api_key():
    api_key_exists = 'ANTHROPIC_API_KEY' in os.environ
    print("api_key_exists",api_key_exists)
    return jsonify({'exists': api_key_exists})

@app.route('/process_abstract', methods=['POST'])
def process_abstract_route():
    abstract = request.json['abstract']
    metrics, cite_forecast, abstract_info = process_abstract(abstract)

    
    return jsonify({
        'metrics': metrics,
        'cite_forecast': cite_forecast['Citation forecast'],
        'abstract_info': abstract_info
    })

@app.route('/random_abstract')
def random_abstract():
    with open('assets/abstracts.txt', 'r') as f:
        abstracts = f.readlines()
    return random.choice(abstracts).strip()

if __name__ == '__main__':
    app.run(debug=True)