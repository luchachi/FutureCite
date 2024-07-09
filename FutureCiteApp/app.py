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
    return jsonify({'exists': api_key_exists})

@app.route('/process_abstract', methods=['POST'])
def process_abstract_route():
    abstract = request.json['abstract']
    api_key = request.headers.get('Anthropic-API-Key')
    
    if not api_key:
        return jsonify({'error': 'API key is required'}), 400

    try:
        metrics, cite_forecast, abstract_info = process_abstract(api_key,abstract)
        return jsonify({
            'metrics': metrics,
            'cite_forecast': cite_forecast['Citation forecast'],
            'abstract_info': abstract_info
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/random_abstract')
def random_abstract():
    with open('assets/abstracts.txt', 'r') as f:
        abstracts = f.readlines()
    return random.choice(abstracts).strip()

if __name__ == '__main__':
    app.run(debug=True)