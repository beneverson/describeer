#!/usr/bin/env python
import logging
import csv
import re
from gensim.models import Doc2Vec
from collections import defaultdict
from numpy import argsort
logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
import describeer_config as dbc
from operator import itemgetter
import cPickle as pickle
import os

import pdb

# variables
_model = None

# lookups
_name_to_style = {}
_name_to_popularity = {}
_name_to_rating = {}

_style_list = []
_name_list = []


def tokenize_beer_noun(beer_noun, reverse=False):
	if reverse: # de-tokenize the term
		return beer_noun.replace('_', ' ')
	return beer_noun.replace(' ', '_')

def init_model(model_path = dbc.DEFAULT_MODEL_PATH):
	global _model
	_model = Doc2Vec.load(model_path)

def init_lookups():

	# global variables
	global _name_to_style
	global _name_to_popularity
	global _name_to_rating
	global _style_list
	global _name_list

	try:
		print "Trying to load pre-pickled data..."
		_name_to_style = pickle.load(open(dbc.DEFAULT_PICKLE_PATH + dbc.name_to_style_path, 'rb'))
		_name_to_popularity = pickle.load(open(dbc.DEFAULT_PICKLE_PATH + dbc.name_to_popularity_path, 'rb'))
		_name_to_rating = pickle.load(open(dbc.DEFAULT_PICKLE_PATH + dbc.name_to_rating_path, 'rb'))
		_style_list = pickle.load(open(dbc.DEFAULT_PICKLE_PATH + dbc.style_list_path, 'rb'))
		_name_list = pickle.load(open(dbc.DEFAULT_PICKLE_PATH + dbc.name_list_path, 'rb'))
		return
	except IOError:
		print "Can't find pickles, loading all data..."


	# local variables
	_name_to_popularity_not_norm = defaultdict(int)
	_name_to_rating_not_norm = defaultdict(float)
	total_reviews = 0 
	max_reviews_any_beer = 0

	# populate the lookups
	with open(dbc.DEFAULT_CSV_PATH, 'rb') as f:
		reader = csv.reader(f)
		next(reader, None) # skip the header
		for row in reader:

			try:
				beer_name = tokenize_beer_noun(row[dbc.name_column])
				beer_style = tokenize_beer_noun(row[dbc.style_column])
				beer_rating = float(row[dbc.overall_score_column])

				# increment this beer's overall popularity
				_name_to_popularity_not_norm[beer_name] += 1 

				# update the max reviews for any one beer
				if _name_to_popularity_not_norm[beer_name] > max_reviews_any_beer:
					max_reviews_any_beer = _name_to_popularity_not_norm[beer_name]

				# increment this beer's overall rating
				_name_to_rating_not_norm[beer_name] += beer_rating

				# init the other lookups
				if beer_name not in _name_to_style.keys():
					_name_to_style[beer_name] = beer_style

				if beer_name not in _name_list:
					_name_list.append(beer_name)

				if beer_style not in _style_list:
					_style_list.append(beer_style)

				total_reviews += 1 # increment total reviews
			
			except ValueError as e:
				print "WARNING: attempt to parse " + str(row)  + " failed. Initialization continuing."

	# populate _name_to_rating with average rating per review for each beer name
	for rated_beer in _name_to_rating_not_norm.keys():
		_name_to_rating[rated_beer] = (1.0 * _name_to_rating_not_norm[rated_beer])/_name_to_popularity_not_norm[rated_beer]

	# populate _name_to_popularity with (# reviews for this beer)/(max # reviews for any beer)
	for reviewed_beer in _name_to_popularity_not_norm.keys():
		_name_to_popularity[reviewed_beer] = (1.0 * _name_to_popularity_not_norm[reviewed_beer])/max_reviews_any_beer

	# pickle the data so we can recall it later
	pickle.dump(_name_to_style, open(str(dbc.DEFAULT_PICKLE_PATH + dbc.name_to_style_path), "w+"))
	pickle.dump(_name_to_popularity, open(str(dbc.DEFAULT_PICKLE_PATH + dbc.name_to_popularity_path), "w+"))
	pickle.dump(_name_to_rating, open(str(dbc.DEFAULT_PICKLE_PATH + dbc.name_to_rating_path), "w+"))
	pickle.dump(_name_list, open(str(dbc.DEFAULT_PICKLE_PATH + dbc.name_list_path), "w+"))
	pickle.dump(_style_list, open(str(dbc.DEFAULT_PICKLE_PATH + dbc.style_list_path), "w+"))


# add/swap additional search terms for every term in lookup_list encountered
# lookup_list = reference list of terms to replace (ex. beer names)
# replacement_dict = dict of new terms to insert/swap in (ex. beer name >> beer style)
def prepare_search_terms(search_terms=[], include_original = True, lookup_list=[], replacement_dict={}):
	prepared_search_terms = [] 
	for term in search_terms:
		tokenized_term = tokenize_beer_noun(term) # tokenize the term
		if tokenized_term in lookup_list:
			prepared_search_terms.append(replacement_dict[tokenized_term])
			if include_original:
				prepared_search_terms.append(tokenized_term)
		else:
			prepared_search_terms.append(tokenized_term)

	return prepared_search_terms

# return list of relevant beers (dicts) for a given positive, negative search query
# TODO: account for the case where no search terms are included
def get_relevant_terms(positive=[], negative=[], use_cosmul = False, returnable_words = []):

	global _name_to_style
	global _name_list

	positive_terms = prepare_search_terms(positive, lookup_list=_name_list, replacement_dict=_name_to_style)
	negative_terms = prepare_search_terms(negative, lookup_list=_name_list, replacement_dict=_name_to_style)
	all_search_terms = positive_terms + negative_terms

	if use_cosmul:
		sims = _model.most_similar_cosmul(positive=positive_terms, negative=negative_terms, topn=len(_model.vocab))
	else:
		sims = _model.most_similar(positive=positive_terms, negative=negative_terms, topn=len(_model.vocab))

	# populate dictionary of terms with assosciated scores
	# filter by returnable_words
	relevant_terms = {}
	for word, score in sims:
		if word in returnable_words and word not in all_search_terms:
			relevant_terms[word] = score

	return relevant_terms


# combine relevant beers, relevant styles, popularity, and average rating to 
# compute a score for each beer passed in
def calculate_beer_score(relevant_beers=[], relevant_styles=[]):
	global _name_to_popularity
	global _name_to_rating
	global _name_to_style

	scored_beers = {}
	for beer_name in relevant_beers.keys():
		beer_style = _name_to_style[beer_name]

		# calculate the score on this beerusing a weighted sum of other scores
		scored_beers[beer_name] = dbc.BEER_SIM_WEIGHT * relevant_beers[beer_name] 
		+ dbc.STYLE_SIM_WEIGHT * relevant_styles[beer_style] 
		+ dbc.BEER_POP_WEIGHT * _name_to_popularity[beer_name]
		+ dbc.BEER_RATING_WEIGHT * _name_to_rating[beer_name]

	# return a sorted list of tuples of scored beers
	return sorted(scored_beers.item(), key=itemgetter(1))

# parse a search term into positive and negative terms
# and feed to get_relevant_terms function
def search_beers(positive_search_terms=[], negative_search_terms=[], n_results = dbc.N_SEARCH_RESULTS):

	# WARNING: assuming positive_search_terms and negative_search_terms are parsed lists already
	# TODO: put parsing logic here, using regex

	# WARNING: hardcoding in some dummy data here
	positive_search_terms = ['Sierra Nevada Pale Ale', 'dark', 'roasty']
	negative_search_terms = ['bitter', 'fruity', 'hoppy']

	# get beer relevance scores
	_relevant_beers = get_relevant_terms(positive=positive_search_terms, negative=negative_search_terms, returnable_words=_name_list)

	# get style relevance scores
	_relevant_styles = get_relevant_terms(positive=positive_search_terms, negative=negative_search_terms, returnable_words=_style_list)

	# figure out the scores for these beers based on above scores
	_scored_beers = calculate_beer_score(relevant_beers=_relevant_beers, relevant_styles=_relevant_styles)

	print _scored_beers[:n_results]


# initialization
def initialize():
	init_model()
	init_lookups()

# TESTING
initialize()
search_beers()
