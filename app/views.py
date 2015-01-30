from flask import render_template, redirect, url_for, request, jsonify
from app import app
from forms import SearchForm
from config import MAX_SEARCH_RESULTS

@app.before_request
def before_request():
	pass

@app.route('/')
@app.route('/index')
def index():
	beernames = []
	for beer in app.beer_model._name_list:
		beerdict = {}
		beerdict['displayname'] = app.beer_model.tokenize_beer_noun(beer.decode('unicode_escape').encode('ascii','ignore'), reverse=True)
		beerdict['value'] = beer.decode('unicode_escape').encode('ascii','ignore')
		beernames.append(beerdict)
	descriptors = app.beer_model._top_descriptors
	return render_template('index.html', title='Home', beernames=beernames, beerdescriptors=descriptors)
	
@app.route('/search', methods=['GET'])
def search():
	positive_terms = request.args.getlist('pos')
	negative_terms = request.args.getlist('neg')

	readable_search_string = '+'.join(positive_terms)
	if(len(negative_terms) > 0):
		readable_search_string = readable_search_string + '-' + '-'.join(negative_terms)
	likely_beers = app.beer_model.search_beers_split(positive_terms, negative_terms)
	return render_template('search_results.html', query=readable_search_string, results=likely_beers)
    
@app.route('/search_results/<query>')
def search_results(query):
	pass