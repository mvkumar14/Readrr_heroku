# from .app import create_app
# NOTE  that when you deploy you have to get rid of the relative
# references so from app instead of from .app
import os
import json

# Third Party Modules
import requests
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS, cross_origin
# from decouple import config #<-- not sure what this does yet

# Custom Modules
from google_books_hf import process_list, gapi_query
# NOTE  that when you deploy you have to get rid of the relative
# references so google_books_hf instead of .google_books_hf

# GLOBAL VARIABLES
# Retreive Google API key from environment
# The AWS instance has to have this environment variable
GOOGLE_KEY = os.environ['GOOGLE_KEY']

# Keys to pull from the google api response
# Eventually this can be read from a file/database for "live"
# modification
relevant_details=['id','title','authors','publisher',
          'publishedDate','description','industryIdentifiers',
          'pageCount','categories','thumbnail','smallThumbnail',
          'language','webReaderLink','textSnippet','isEbook',
          'averageRating']


application = Flask(__name__)
CORS(application,supports_credentials=True)

@application.route('/')
# some details about the api and some references
# to api documentation
def root():
    return render_template('base.html',page_name='home')


@application.route('/test',methods=['POST'])
def test():
    print('test')
    test_val = request.get_json(force=True)
    print(test_val)
    return "this is a test page"


@application.route('/search', methods=['POST'])
@cross_origin(supports_credentials=True)
def search():
    input_data = request.get_json(force=True)
    try:
        startIndex = input_data['startIndex']
    except KeyError:
        startIndex = 0
    try:
        maxResults = input_data['maxResults']
    except KeyError:
        maxResults = 10
    # Try to access keys from the post request
    try:
        if input_data['type'] == 'googleId':
            search_id = input_data['query']
            response = requests.get('https://www.googleapis.com/books/v1/volumes/'
                                    + search_id
                                    + '?key='
                                    + GOOGLE_KEY)
            # If invalid google id, then display/return an error message
            result = json.loads(response.text)
            output = process_list([result],relevant_details)
            return jsonify(output)

        elif input_data['type'] == 'search':
            search_term = input_data['query']
            result = gapi_query(search_term,startIndex,maxResults)
            totalItems = result['totalItems']
            item_list = process_list(result['items'],relevant_details)
            output = {'totalItems':totalItems,'items':item_list}
            return jsonify(output)
        else:
            message = """ The value for the 'type' key was invalid.
             Please change the value to 'googleId', or 'search' """
            return render_template('echo.html',page_name='error',
                                    echo=message)
    # If you can't access keys from the post request display error message
    except KeyError:
        message = """ The key wasn't in the request body"""
        return render_template('echo.html',page_name='error', echo=message)

    return render_template('echo.html',page_name='search')


@application.route('/recommendations',methods=['POST'])
@cross_origin(supports_credentials=True)
# input is ???
# The input might include parameters that aid in the model
# selection process. We may have different models depending on
# the different types of recommendations we need to provide.
# output is a list of books.
def recommendations():
    cwd = os.getcwd()
    print(cwd)
    with open('hardcode_reccs.json','r',encoding='utf8') as f :
        output = json.load(f)
    return jsonify(output)

if __name__ == '__main__':
    application.run(debug=True)
